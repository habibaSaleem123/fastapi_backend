from fastapi import HTTPException, status, Request, Depends
from app.core.security.jwt import decode_token

def get_bearer_token(req: Request) -> str:
    auth = req.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    return auth.split(" ", 1)[1]

def get_current_user(token: str = Depends(get_bearer_token)):
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise ValueError("Wrong token type")
        return {
            "id": payload["sub"],
            "roles": payload.get("roles", []),
            "permissions": payload.get("perms", []),
        }
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

REFRESH_COOKIE_NAME = "refresh_token"

def get_refresh_cookie(req: Request) -> str | None:
    return req.cookies.get(REFRESH_COOKIE_NAME)
