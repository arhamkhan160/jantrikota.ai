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

    # ── LLM (OpenAI-compatible: OpenAI, Groq, OpenRouter, Together, local) ──
    LLM_API_KEYS: str = ""             # comma-separated; round-robined per call
    LLM_API_KEY: str = ""              # single key (used if LLM_API_KEYS is blank)
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_BASE_URL: str = ""             # blank = OpenAI default; set for Groq/OpenRouter

    # ── Embeddings (for semantic dataset-search ranking) ───────────────────
    EMBED_MODEL: str = "text-embedding-3-small"
    EMBED_API_KEY: str = ""             # blank = reuse LLM_API_KEY
    EMBED_BASE_URL: str = ""            # blank = reuse LLM_BASE_URL

    # ── CORS ───────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
