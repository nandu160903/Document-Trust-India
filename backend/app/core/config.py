"""Application settings loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ — parent of the app package
BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Central configuration for DocumentTrust India backend."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "DocumentTrust India"
    app_version: str = "0.1.0"
    debug: bool = True

    # CORS origins for local React frontends (CRA / Vite)
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Upload storage
    upload_dir: Path = BASE_DIR / "temp" / "uploads"
    max_upload_size_mb: int = 10
    allowed_content_types: list[str] = [
        "image/jpeg",
        "image/png",
        "application/pdf",
    ]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    settings = Settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    return settings
