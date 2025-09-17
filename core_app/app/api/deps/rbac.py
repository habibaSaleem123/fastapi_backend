from fastapi import Depends, HTTPException, status
from app.api.deps.auth import get_current_user
from app.db.models.role import Role

async def _permissions_from_roles(role_slugs: list[str]) -> set[str]:
    if not role_slugs:
        return set()
    roles = await Role.find(Role.slug.in_(role_slugs)).to_list()
    perms: set[str] = set()
    for r in roles:
        perms.update(r.permissions or [])
    return perms

def require_roles(required: list[str], *, fresh: bool = False):
    async def dep(user=Depends(get_current_user)):
        roles = set(user.get("roles", []))
        if not set(required).issubset(roles):
            # Optionally re-fetch if fresh=True (omitted here for simplicity)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing required role")
        return user
    return dep

def require_perms(required: list[str], *, fresh: bool = False):
    async def dep(user=Depends(get_current_user)):
        token_perms = set(user.get("permissions", []))
        if fresh:
            # Recompute from DB to avoid stale token permissions
            token_roles = user.get("roles", [])
            token_perms = await _permissions_from_roles(token_roles)
        if not set(required).issubset(token_perms):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing required permission")
        return user
    return dep
