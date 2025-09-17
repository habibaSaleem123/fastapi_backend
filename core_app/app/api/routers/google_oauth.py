from fastapi import APIRouter, HTTPException, Depends, Request, Response, Query
from datetime import datetime, timezone
import httpx
import jwt
from jwt import PyJWKClient
from urllib.parse import urlencode

from app.core.config.settings import settings
from app.core.ratelimit.limiter import rate_limit
from app.db.repositories.users import UsersRepo
from app.db.repositories.oauth_accounts import OAuthAccountsRepo
from app.db.repositories.refresh_tokens import RefreshTokensRepo
from app.core.security.jwt import create_access_token, create_refresh_token, decode_token
from app.api.deps.auth import REFRESH_COOKIE_NAME
from app.utils.oauth_state import make_oauth_state, parse_oauth_state

router = APIRouter(prefix="/auth/google", tags=["auth:google"])

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
ISS_TRUSTED = {"https://accounts.google.com", "accounts.google.com"}

def cookie_opts():
    samesite = settings.COOKIE_SAMESITE.lower()
    return dict(
        httponly=True,
        samesite=("none" if samesite == "none" else "lax" if samesite == "lax" else "strict"),
        secure=bool(settings.COOKIE_SECURE),
        domain=settings.COOKIE_DOMAIN,
        max_age=settings.REFRESH_TOKEN_TTL_DAYS * 86400,
        path="/",
    )

def _require_google_config():
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_REDIRECT_URI:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")

@router.get("/start", dependencies=[Depends(rate_limit("30/min", "google_start"))])
async def google_start():
    """
    Returns the Google authorization URL (we do not redirect automatically to keep it API-friendly).
    """
    _require_google_config()

    state = make_oauth_state()
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        # You can add 'nonce' too if you want to bind explicitly; we embed nonce into state already.
        # "nonce": <from state if you extract it>,
        "access_type": "offline",  # may return refresh_token from Google if needed
        "prompt": "consent",       # ensure consent screen & refresh on each try during dev
    }
    return {
        "auth_url": f"{AUTH_URL}?{urlencode(params)}",
        "state": state,
    }

@router.get("/callback", dependencies=[Depends(rate_limit("60/min", "google_callback"))])
async def google_callback(request: Request, response: Response, code: str = Query(...), state: str = Query(...)):
    """
    Handles Google's callback: exchange code->tokens, validate id_token, link or create user, issue our JWTs.
    """
    _require_google_config()

    # 1) Validate state (signed by our backend)
    try:
        state_payload = parse_oauth_state(state)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid state")

    # 2) Exchange code for tokens
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    # If you are not using PKCE from a SPA, include client_secret here:
    if settings.GOOGLE_CLIENT_SECRET:
        data["client_secret"] = settings.GOOGLE_CLIENT_SECRET

    async with httpx.AsyncClient(timeout=15) as client:
        token_res = await client.post(TOKEN_URL, data=data)
    if token_res.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {token_res.text}")

    token_json = token_res.json()
    id_token = token_json.get("id_token")
    if not id_token:
        raise HTTPException(status_code=400, detail="No id_token from Google")

    # 3) Validate id_token signature & claims
    jwk_client = PyJWKClient(JWKS_URL)
    try:
        signing_key = jwk_client.get_signing_key_from_jwt(id_token)
        decoded = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.GOOGLE_CLIENT_ID,
            options={"require": ["exp", "iat", "aud", "iss", "sub"]},
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"id_token validation failed: {e}")

    iss = decoded.get("iss")
    if iss not in ISS_TRUSTED:
        raise HTTPException(status_code=400, detail="Untrusted issuer")
    # You can also validate 'nonce' if you included it in the auth URL and state:
    # if decoded.get("nonce") != state_payload.get("nonce"):
    #     raise HTTPException(status_code=400, detail="Nonce mismatch")

    sub = decoded.get("sub")
    email = decoded.get("email")
    email_verified = decoded.get("email_verified")
    name = decoded.get("name")
    picture = decoded.get("picture")

    if not sub:
        raise HTTPException(status_code=400, detail="Missing subject in id_token")
    if not email or not email_verified:
        raise HTTPException(status_code=403, detail="Google email not verified")

    # 4) Link or create local user
    users = UsersRepo()
    oauths = OAuthAccountsRepo()

    # Find by provider-sub first
    link = await oauths.get_by_provider_sub("google", sub)
    if link:
        user = await users.get_by_email(link.email) if link.email else None
        if not user:
            # Fallback fetch by id
            from app.db.models import User
            user = await User.get(link.user_id)
    else:
        # No link yet -> check if we already have a user with this email
        user = await users.get_by_email(email)
        if not user:
            if not settings.OAUTH_ALLOW_SIGNUP:
                raise HTTPException(status_code=403, detail="Signup via Google disabled")
            # Create local user; mark verified
            user = await users.create(email=email, password="!", full_name=name or email.split("@")[0])
            from app.db.models import User as UserModel
            user_model = await UserModel.get(user.id)
            user_model.email_verified_at = datetime.utcnow()
            await user_model.save()
        # Create link
        await oauths.create_link(
            provider="google",
            provider_sub=sub,
            user_id=user.id,
            email=email,
            name=name,
            picture=picture,
        )

    # 5) Issue our tokens (same flow as /login)
    roles = await users.get_roles(user.id)
    perms = await users.get_permissions(user.id)
    access = create_access_token(sub=user.id, roles=roles, perms=perms)

    refresh = create_refresh_token(sub=user.id)
    r_payload = decode_token(refresh)
    exp_dt = datetime.fromtimestamp(r_payload["exp"], tz=timezone.utc)

    ua = request.headers.get("user-agent", "")
    ip = request.client.host if request.client else None
    await RefreshTokensRepo().store(
        jti=r_payload["jti"], user_id=user.id, raw_token=refresh,
        expires_at=exp_dt, user_agent=ua, ip=ip
    )

    response.set_cookie(REFRESH_COOKIE_NAME, refresh, **cookie_opts())
    return {
        "access_token": access,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": name or user.full_name,
            "roles": roles,
            "permissions": perms,
            "provider": "google",
        },
    }
