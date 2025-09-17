from datetime import datetime
from beanie import Document, Indexed
from pydantic import Field

class Role(Document):
    slug: Indexed(str, unique=True)  # e.g., "admin", "user"
    permissions: list[str] = []      # e.g., ["users:read", "users:write"]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "roles"
