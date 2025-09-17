# app/core/config/settings.py
from __future__ import annotations

import json
import math
import os
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_list(val: str | None) -> List[str]:
    """
    Accept JSON list or comma-separated string.
    """
    if not val:
        return []
    v = val.strip()
    if v.startswith("["):
        try:
            parsed = json.loads(v)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except Exception:
            pass
    # fallback: comma-separated
    return [x.strip() for x in v.split(",") if x.strip()]


class Settings(BaseSettings):
    # Allow unknown env keys so Pydantic doesn't crash when old keys are present
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    APP_NAME: str = "core_app"
    ENV: str = "dev"
    API_PREFIX: str = Field("/api", validation_alias="API_PREFIX")  # legacy: api_prefix handled below

    # --- Security / JWT ---
    # Keep a dev default to avoid crashes; you can remove default to force requirement in prod
    JWT_SECRET: str = "change-this-in-prod"
    JWT_ALG: str = Field("HS256", validation_alias="JWT_ALG")  # legacy: jwt_alg handled below
    ACCESS_TOKEN_TTL_MIN: int = 20
    REFRESH_TOKEN_TTL_DAYS: int = 7
    LOGIN_REQUIRE_VERIFIED: bool = False
    # Legacy seconds (optional) — if set, they override the minute/day fields
    ACCESS_TTL_SECONDS: Optional[int] = Field(default=None, validation_alias="ACCESS_TTL_SECONDS")
    REFRESH_TTL_SECONDS: Optional[int] = Field(default=None, validation_alias="REFRESH_TTL_SECONDS")

    # --- CORS / Cookies ---
    FRONTEND_ORIGIN: str = "http://localhost:3000"
    CORS_ORIGINS: List[str] = Field(default_factory=list)
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"   # lax | none | strict
    COOKIE_DOMAIN: Optional[str] = None

    # --- Database (Mongo) ---
    MONGO_URI: str
    MONGO_DB_NAME: str = "core_db"
    
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = None
    OAUTH_ALLOW_SIGNUP: bool = True
    # --- Frontend deep links ---
    FRONTEND_URL: str = "http://localhost:3000"
    VERIFY_PATH: str = "/verify-email"
    RESET_PATH: str = "/reset-password"

    # --- Email (SMTP) ---
    MAIL_FROM: str = "noreply@yourapp.dev"
    MAIL_FROM_NAME: str = "Your App"
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASS: Optional[str] = None
    SMTP_TLS: bool = True

    # --- Rate limits (count/window_seconds) ---
    RATE_LIMIT_LOGIN: str = "5/300"
    RATE_LIMIT_SIGNUP: str = "3/1800"
    RATE_LIMIT_FORGOT: str = "3/900"
    RATE_LIMIT_VERIFY_REQUEST: str = "5/1800"

    # --- Password policy ---
    MIN_PASSWORD_LENGTH: int = 8
    MIN_PASSWORD_SCORE: int = 3

    # ---------- Validators / Legacy mapping ----------

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _load_cors_origins(cls, v):
        # Prefer CORS_ORIGINS env; else fallback to legacy cors_origins
        if v:
            if isinstance(v, list):
                return v
            return _parse_list(str(v))
        legacy = os.getenv("cors_origins")
        if legacy:
            return _parse_list(legacy)
        # default: derive from FRONTEND_ORIGIN if set
        fallback = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
        return [fallback] if fallback else []

    def model_post_init(self, __context):
        # api_prefix -> API_PREFIX
        legacy_api = os.getenv("api_prefix")
        if legacy_api:
            self.API_PREFIX = legacy_api

        # jwt_alg -> JWT_ALG
        legacy_alg = os.getenv("jwt_alg")
        if legacy_alg:
            self.JWT_ALG = legacy_alg

        # access_ttl_seconds / refresh_ttl_seconds -> minutes/days (override if provided)
        legacy_access = os.getenv("access_ttl_seconds")
        if legacy_access:
            try:
                secs = int(legacy_access)
                self.ACCESS_TOKEN_TTL_MIN = max(1, math.ceil(secs / 60))
            except Exception:
                pass
        elif self.ACCESS_TTL_SECONDS is not None:
            self.ACCESS_TOKEN_TTL_MIN = max(1, math.ceil(int(self.ACCESS_TTL_SECONDS) / 60))

        legacy_refresh = os.getenv("refresh_ttl_seconds")
        if legacy_refresh:
            try:
                secs = int(legacy_refresh)
                self.REFRESH_TOKEN_TTL_DAYS = max(1, math.ceil(secs / 86400))
            except Exception:
                pass
        elif self.REFRESH_TTL_SECONDS is not None:
            self.REFRESH_TOKEN_TTL_DAYS = max(1, math.ceil(int(self.REFRESH_TTL_SECONDS) / 86400))


# Export singleton
settings = Settings()
