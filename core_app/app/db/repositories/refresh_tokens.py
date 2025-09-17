import hashlib
from datetime import datetime
from app.db.models import RefreshToken

def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

class RefreshTokensRepo:
    def __init__(self, *_):
        pass

    async def store(self, jti: str, user_id: str, raw_token: str, expires_at: datetime, user_agent: str | None, ip: str | None):
        rec = RefreshToken(
            jti=jti,
            user_id=user_id,
            token_hash=_sha256(raw_token),
            expires_at=expires_at,  # UTC
            user_agent=(user_agent[:255] if user_agent else None),
            ip=ip,
        )
        await rec.insert()

    async def get_valid(self, jti: str) -> RefreshToken | None:
        # Use raw query to avoid operator issues
        return await RefreshToken.find_one({"jti": jti, "revoked_at": None})

    async def revoke(self, jti: str):
        await RefreshToken.find({"jti": jti}).update({"$set": {"revoked_at": datetime.utcnow()}})

    async def revoke_all_for_user(self, user_id: str):
        # Update many with raw query (no '&' composition)
        await RefreshToken.find({"user_id": user_id, "revoked_at": None}).update(
            {"$set": {"revoked_at": datetime.utcnow()}}
        )

    def matches(self, rec: RefreshToken, raw_token: str) -> bool:
        return rec.token_hash == _sha256(raw_token)
