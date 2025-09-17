from app.db.models import OAuthAccount

class OAuthAccountsRepo:
    def __init__(self, *_):
        pass

    async def get_by_provider_sub(self, provider: str, provider_sub: str) -> OAuthAccount | None:
        return await OAuthAccount.find_one({"provider": provider, "provider_sub": provider_sub})

    async def create_link(
        self, *, provider: str, provider_sub: str, user_id: str,
        email: str | None, name: str | None, picture: str | None
    ) -> OAuthAccount:
        doc = OAuthAccount(
            provider=provider, provider_sub=provider_sub, user_id=user_id,
            email=email, name=name, picture=picture
        )
        await doc.insert()
        return doc
