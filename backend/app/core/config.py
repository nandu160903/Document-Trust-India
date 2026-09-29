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

    # Server bind address (default: 7676)
    api_host: str = "0.0.0.0"
    api_port: int = 7676

    # CORS origins for local React frontends (CRA / Vite)
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Upload storage
    upload_dir: Path = BASE_DIR / "temp" / "uploads"
    heatmap_dir: Path = BASE_DIR / "temp" / "heatmaps"
    max_upload_size_mb: int = 10
    allowed_content_types: list[str] = [
        "image/jpeg",
        "image/png",
        "application/pdf",
    ]

    # Forensic analysis defaults
    ela_jpeg_quality: int = 92
    ela_amplification_factor: float = 10.0
    ela_mean_error_threshold: float = 8.0
    ela_peak_anomaly_threshold: float = 2.5

    # Deep learning inference
    enable_transformers_inference: bool = True
    hf_model_id: str = "google/vit-base-patch16-224"

    # Risk engine weights and thresholds
    risk_weight_metadata: int = 25
    risk_weight_ela: int = 30
    risk_weight_layout: int = 20
    risk_weight_deep_learning: int = 25
    dl_anomaly_threshold: float = 0.7
    risk_level_low_max: int = 29
    risk_level_medium_max: int = 65


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    settings = Settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.heatmap_dir.mkdir(parents=True, exist_ok=True)
    return settings
