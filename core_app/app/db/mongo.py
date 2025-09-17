# app/db/mongo.py
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.core.config.settings import settings
from app.db.models.user import User
from app.db.models.refresh_token import RefreshToken
from app.db.models.oauth_account import OAuthAccount
from app.db.models.role import Role  # keep if you actually have this model

_mongo_client: Optional[AsyncIOMotorClient] = None


async def init_mongo() -> None:
    """
    Connect to MongoDB and initialize Beanie with all document models.
    Call this once on app startup.
    """
    global _mongo_client
    _mongo_client = AsyncIOMotorClient(settings.MONGO_URI)
    db = _mongo_client[settings.MONGO_DB_NAME]

    await init_beanie(
        database=db,
        document_models=[
            User,
            RefreshToken,
            OAuthAccount,
            Role,  # or comment out if not using
        ],
    )

    # TTL index for refresh tokens
    await db["refresh_tokens"].create_index("expires_at", expireAfterSeconds=0)


def get_client() -> AsyncIOMotorClient:
    if _mongo_client is None:
        raise RuntimeError("Mongo client not initialized")
    return _mongo_client
