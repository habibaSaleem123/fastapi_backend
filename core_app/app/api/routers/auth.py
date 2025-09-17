# app/api/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, Response, Request, status, Query
from datetime import datetime, timezone
from app.db.repositories.users import UsersRepo
from app.db.repositories.refresh_tokens import RefreshTokensRepo
from app.core.security.passwords import verify_password, hash_password
from app.core.security.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    create_verify_email_token,
    create_reset_password_token,
)
from app.core.config.settings import settings
from app.schemas.auth import (
    SignupIn, LoginIn, LoginOut, RefreshOut,
    VerifyRequestIn, ForgotPasswordIn, ResetPasswordIn,
)
from app.api.deps.auth import REFRESH_COOKIE_NAME, get_refresh_cookie
from app.core.ratelimit.limiter import rate_limit
from app.utils.emails import get_email_sender, build_frontend_link
from app.utils.password_strength import validate_password_strength, PasswordTooWeak
from app.db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

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

@router.post("/signup", status_code=201, dependencies=[Depends(rate_limit(settings.RATE_LIMIT_SIGNUP, "signup"))])
async def signup(payload: SignupIn):
    users = UsersRepo()
    existing = await users.get_by_email(payload.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already in use")

    try:
        validate_password_strength(payload.password, user_inputs=[payload.email, payload.full_name])
    except PasswordTooWeak as e:
        raise HTTPException(status_code=400, detail={"message": str(e), "score": e.score, "feedback": e.feedback})

    user = await users.create(email=payload.email, password=payload.password, full_name=payload.full_name)

    token = create_verify_email_token(sub=user.id, email=user.email)
    link_fe = build_frontend_link(settings.VERIFY_PATH, token)
    link_be = f"/auth/verify/confirm?token={token}"
    sender = get_email_sender()
    await sender.send(
        to=user.email,
        subject="Verify your email",
        html=f"<p>Welcome {user.full_name}!</p><p>Verify: <a href='{link_fe}'>{link_fe}</a></p><p>Or direct (backend): <code>{link_be}</code></p>",
        text=f"Welcome {user.full_name}! Verify: {link_fe}",
    )

    return {"id": user.id, "email": user.email, "full_name": user.full_name}

@router.post("/login", response_model=LoginOut, dependencies=[Depends(rate_limit(settings.RATE_LIMIT_LOGIN, "login"))])
async def login(payload: LoginIn, request: Request, response: Response):
    users = UsersRepo()
    rtrepo = RefreshTokensRepo()
    user = await users.get_by_email(payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if settings.LOGIN_REQUIRE_VERIFIED and not user.email_verified_at:
        raise HTTPException(status_code=403, detail="Email not verified")

    roles = await users.get_roles(user.id)
    perms = await users.get_permissions(user.id)
    access = create_access_token(sub=user.id, roles=roles, perms=perms)

    refresh = create_refresh_token(sub=user.id)
    r_payload = decode_token(refresh)
    exp_dt = datetime.fromtimestamp(r_payload["exp"], tz=timezone.utc)

    ua = request.headers.get("user-agent", "")
    ip = request.client.host if request.client else None
    await rtrepo.store(jti=r_payload["jti"], user_id=user.id, raw_token=refresh, expires_at=exp_dt, user_agent=ua, ip=ip)

    response.set_cookie(REFRESH_COOKIE_NAME, refresh, **cookie_opts())
    return {
        "access_token": access,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.full_name,
            "roles": roles,
            "permissions": perms,
            "verified": bool(user.email_verified_at),
        },
    }

@router.post("/refresh", response_model=RefreshOut)
async def refresh(request: Request, response: Response):
    cookie = get_refresh_cookie(request)
    if not cookie:
        raise HTTPException(status_code=401, detail="No refresh token")
    try:
        payload = decode_token(cookie)
        if payload.get("type") != "refresh":
            raise ValueError("Wrong token type")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    rtrepo = RefreshTokensRepo()
    rec = await rtrepo.get_valid(payload["jti"])
    if not rec or not rtrepo.matches(rec, cookie):
        raise HTTPException(status_code=401, detail="Refresh token not found or revoked")

    await rtrepo.revoke(payload["jti"])

    new_refresh = create_refresh_token(sub=payload["sub"])
    new_payload = decode_token(new_refresh)
    await rtrepo.store(
        jti=new_payload["jti"],
        user_id=payload["sub"],
        raw_token=new_refresh,
        expires_at=datetime.fromtimestamp(new_payload["exp"], tz=timezone.utc),
        user_agent=request.headers.get("user-agent", ""),
        ip=request.client.host if request.client else None,
    )

    users = UsersRepo()
    roles = await users.get_roles(payload["sub"])
    perms = await users.get_permissions(payload["sub"])
    access = create_access_token(sub=payload["sub"], roles=roles, perms=perms)

    response.set_cookie(REFRESH_COOKIE_NAME, new_refresh, **cookie_opts())
    return {"access_token": access}

@router.post("/logout", status_code=204)
async def logout(request: Request, response: Response):
    cookie = get_refresh_cookie(request)
    if cookie:
        try:
            payload = decode_token(cookie)
            if payload.get("type") == "refresh":
                rtrepo = RefreshTokensRepo()
                await rtrepo.revoke(payload["jti"])
        except Exception:
            pass
    response.delete_cookie(REFRESH_COOKIE_NAME, path="/", domain=settings.COOKIE_DOMAIN)

# ----- Email verification -----

@router.post("/verify/request", dependencies=[Depends(rate_limit(settings.RATE_LIMIT_VERIFY_REQUEST, "verify_request"))])
async def verify_request(payload: VerifyRequestIn):
    users = UsersRepo()
    user = await users.get_by_email(payload.email)
    if user and not user.email_verified_at:
        token = create_verify_email_token(sub=user.id, email=user.email)
        link_fe = build_frontend_link(settings.VERIFY_PATH, token)
        link_be = f"/auth/verify/confirm?token={token}"
        sender = get_email_sender()
        await sender.send(
            to=user.email,
            subject="Verify your email",
            html=f"<p>Verify your email:</p><p><a href='{link_fe}'>{link_fe}</a></p><p>Or backend direct: <code>{link_be}</code></p>",
            text=f"Verify your email: {link_fe}",
        )
    return {"ok": True}

@router.get("/verify/confirm")
async def verify_confirm(token: str = Query(...)):
    try:
        payload = decode_token(token)
        if payload.get("type") != "verify-email":
            raise ValueError("Wrong token type")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    uid = payload["sub"]
    user = await User.get(uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.email_verified_at:
        user.email_verified_at = datetime.utcnow()
        await user.save()
    return {"verified": True}

# ----- Password reset -----

@router.post("/password/forgot", dependencies=[Depends(rate_limit(settings.RATE_LIMIT_FORGOT, "forgot"))])
async def password_forgot(payload: ForgotPasswordIn):
    users = UsersRepo()
    user = await users.get_by_email(payload.email)
    if user:
        token = create_reset_password_token(sub=user.id)
        link_fe = build_frontend_link(settings.RESET_PATH, token)
        link_be = f"/auth/password/reset?token={token}&new_password=<your_new_password>"
        sender = get_email_sender()
        await sender.send(
            to=user.email,
            subject="Reset your password",
            html=f"<p>Reset password:</p><p><a href='{link_fe}'>{link_fe}</a></p><p>Dev direct (backend): <code>{link_be}</code></p>",
            text=f"Reset password: {link_fe}",
        )
    return {"ok": True}

@router.post("/password/reset")
async def password_reset(payload: ResetPasswordIn):
    try:
        decoded = decode_token(payload.token)
        if decoded.get("type") != "reset-password":
            raise ValueError("Wrong token type")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    try:
        validate_password_strength(payload.new_password)
    except PasswordTooWeak as e:
        raise HTTPException(status_code=400, detail={"message": str(e), "score": e.score, "feedback": e.feedback})

    uid = decoded["sub"]
    user = await User.get(uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(payload.new_password)
    user.updated_at = datetime.utcnow()
    await user.save()

    rtrepo = RefreshTokensRepo()
    await rtrepo.revoke_all_for_user(uid)

    return {"reset": True}
