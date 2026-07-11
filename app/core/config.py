"""
core/config.py
Application settings loaded from environment variables via pydantic-settings.
Swap DB_URL / SUPABASE_* values when connecting to Supabase.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    # ── General ────────────────────────────────────────────────────────────
    APP_NAME: str = "AutoML Agent"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # ── Logging ────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "info"

    # ── Storage ────────────────────────────────────────────────────────────
    MODEL_DIR: str = "./models"
    DATASET_DIR: str = "./datasets"

    # ── ML (FLAML owns model search/tuning; these are the only knobs) ───────
    TIME_BUDGET_SECONDS: int = 30       # FLAML AutoML search budget per job
    RANDOM_STATE: int = 42

    # ── CORS ───────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
