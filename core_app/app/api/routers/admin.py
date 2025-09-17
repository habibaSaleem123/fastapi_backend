from fastapi import APIRouter, HTTPException, Depends
from app.api.deps.rbac import require_perms
from app.db.models.role import Role
from app.db.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])

# Manage roles (requires roles:manage)
@router.post("/roles", dependencies=[Depends(require_perms(["roles:manage"]))])
async def create_role(slug: str, permissions: list[str]):
    existing = await Role.find_one(Role.slug == slug)
    if existing:
        raise HTTPException(status_code=409, detail="Role already exists")
    r = Role(slug=slug, permissions=permissions)
    await r.insert()
    return {"id": str(r.id), "slug": r.slug, "permissions": r.permissions}

@router.get("/roles", dependencies=[Depends(require_perms(["roles:manage"]))])
async def list_roles():
    roles = await Role.find_all().to_list()
    return [{"id": str(r.id), "slug": r.slug, "permissions": r.permissions} for r in roles]

@router.post("/users/{user_id}/roles:add", dependencies=[Depends(require_perms(["roles:manage"]))])
async def add_role_to_user(user_id: str, slug: str):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if slug not in (user.roles or []):
        user.roles = (user.roles or []) + [slug]
        await user.save()
    return {"id": user.id, "roles": user.roles}

@router.post("/users/{user_id}/roles:remove", dependencies=[Depends(require_perms(["roles:manage"]))])
async def remove_role_from_user(user_id: str, slug: str):
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.roles = [s for s in (user.roles or []) if s != slug]
    await user.save()
    return {"id": user.id, "roles": user.roles}
