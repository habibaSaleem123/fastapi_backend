# app/api/routers/__init__.py
from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .admin import router as admin_router
from .dev import router as dev_router  # <-- make sure this line exists
from .google_oauth import router as google_router 

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(admin_router)
api_router.include_router(dev_router)   # <-- and this one too
api_router.include_router(google_router) 