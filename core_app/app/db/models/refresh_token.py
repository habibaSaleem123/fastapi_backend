from datetime import datetime
from typing import Optional

from beanie import Document, Indexed
from pydantic import Field

class RefreshToken(Document):
    # Keep a separate indexed JTI field (not using it as _id)
    jti: Indexed(str, unique=True)
    user_id: str
    token_hash: str
    user_agent: Optional[str] = None
    ip: Optional[str] = None
    expires_at: datetime  # TTL index created in init_mongo()
    revoked_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "refresh_tokens"
