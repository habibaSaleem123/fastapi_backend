from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.logging_config import configure_logging
from app.core.config.settings import settings
from app.api.routers import api_router
from app.db.mongo import init_mongo

configure_logging()
app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    await init_mongo()

app.include_router(api_router)

@app.get("/healthz")
async def healthz():
    return {"ok": True}
