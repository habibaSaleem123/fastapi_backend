from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
import jwt
from app.core.config.settings import settings
from app.utils.ids import new_uuid

ALGO = "HS256"

def _now():
    return datetime.now(timezone.utc)

def create_access_token(sub: str, roles: List[str], perms: List[str]) -> str:
    exp = _now() + timedelta(minutes=settings.ACCESS_TOKEN_TTL_MIN)
    payload: Dict[str, Any] = {
        "sub": sub,
        "roles": roles,
        "perms": perms,
        "type": "access",
        "jti": new_uuid(),
        "iat": int(_now().timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGO)

def create_refresh_token(sub: str, jti: str | None = None, days: int | None = None) -> str:
    exp = _now() + timedelta(days=days or settings.REFRESH_TOKEN_TTL_DAYS)
    payload = {
        "sub": sub,
        "type": "refresh",
        "jti": jti or new_uuid(),
        "iat": int(_now().timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGO)

def create_verify_email_token(sub: str, email: str, hours: int = 24) -> str:
    exp = _now() + timedelta(hours=hours)
    payload = {
        "sub": sub,
        "email": email,
        "type": "verify-email",
        "jti": new_uuid(),
        "iat": int(_now().timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGO)

def create_reset_password_token(sub: str, hours: int = 1) -> str:
    exp = _now() + timedelta(hours=hours)
    payload = {
        "sub": sub,
        "type": "reset-password",
        "jti": new_uuid(),
        "iat": int(_now().timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGO)

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGO])
