from datetime import datetime, timedelta, timezone
import jwt
from app.core.config.settings import settings
from app.utils.ids import new_uuid

ALGO = "HS256"

def _now():
    return datetime.now(timezone.utc)

def make_oauth_state(nonce: str | None = None, minutes: int = 10) -> str:
    payload = {
        "type": "oauth-state",
        "nonce": nonce or new_uuid(),
        "iat": int(_now().timestamp()),
        "exp": int((_now() + timedelta(minutes=minutes)).timestamp()),
        "jti": new_uuid(),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGO)

def parse_oauth_state(token: str) -> dict:
    data = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGO])
    if data.get("type") != "oauth-state":
        raise ValueError("bad state type")
    return data
