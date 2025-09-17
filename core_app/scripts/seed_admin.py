import asyncio
from app.db.mongo import init_mongo
from app.db.models.user import User
from app.db.models.role import Role

ADMIN_ROLE = {
    "slug": "admin", #
    "permissions": ["users:read", "users:write", "roles:manage"]
}

async def main():
    await init_mongo()
    # ensure admin role
    r = await Role.find_one(Role.slug == ADMIN_ROLE["slug"])
    if not r:
        r = Role(**ADMIN_ROLE)
        await r.insert()
        print("Created role 'admin'")

    # pick a user by email to promote
    email = "alice@example.com"  # <-- change
    u = await User.find_one(User.email == email)
    if not u:
        print("User not found:", email)
        return
    if "admin" not in (u.roles or []):
        u.roles = (u.roles or []) + ["admin"]
        await u.save()
        print("Added 'admin' to user:", email)
    else:
        print("User already admin:", email)

if __name__ == "__main__":
    asyncio.run(main())
