# app/db/models/oauth_account.py
from datetime import datetime
from typing import Optional
from beanie import Document, Indexed

class OAuthAccount(Document):
    provider: str                 # "google"
    provider_sub: Indexed(str)    # Google's stable user id (sub)
    user_id: str                  # your local User.id

    # cached profile bits (optional)
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None

    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

    class Settings:
        name = "oauth_accounts"
        indexes = [
            [("provider", 1), ("provider_sub", 1)],  # compound index
            "user_id",
        ]
