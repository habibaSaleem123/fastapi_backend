from app.db.models import User, Role
from app.core.security.passwords import hash_password

# If you prefer the operator version, uncomment the next line and the 'In' usage below.
# from beanie.operators import In

class UsersRepo:
    def __init__(self, *_):
        pass

    async def get_by_email(self, email: str) -> User | None:
        return await User.find_one(User.email == email)

    async def create(self, email: str, password: str, full_name: str) -> User:
        user = User(email=email, full_name=full_name, hashed_password=hash_password(password))
        await user.insert()
        return user

    async def get_roles(self, user_id: str) -> list[str]:
        u = await User.get(user_id)
        return (u.roles if u else []) or []

    async def get_permissions(self, user_id: str) -> list[str]:
        u = await User.get(user_id)
        if not u or not u.roles:
            return []

        # --- Option A: raw $in (most compatible) ---
        roles = await Role.find({"slug": {"$in": u.roles}}).to_list()

        # --- Option B: operator API (works on recent Beanie) ---
        # roles = await Role.find(In(Role.slug, u.roles)).to_list()

        perms: set[str] = set()
        for r in roles:
            perms.update(r.permissions or [])
        return sorted(perms)
