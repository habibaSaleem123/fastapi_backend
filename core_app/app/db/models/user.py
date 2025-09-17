from datetime import datetime
from typing import Optional
from beanie import Document, Indexed
from pydantic import Field, EmailStr
from app.utils.ids import new_uuid

class User(Document):
    id: str = Field(default_factory=new_uuid)  # Mongo _id
    email: Indexed(EmailStr, unique=True)
    full_name: str
    hashed_password: str
    is_active: bool = True
    email_verified_at: Optional[datetime] = None
    roles: list[str] = Field(default_factory=lambda: ["user"])  # NEW: role slugs
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"
