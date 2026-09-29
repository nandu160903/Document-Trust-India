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
    temp_dir: Path = BASE_DIR / "temp"
    static_uploads_prefix: str = "/static/uploads"
    static_heatmaps_prefix: str = "/static/heatmaps"
    max_upload_size_mb: int = 10
    allowed_content_types: list[str] = [
        "image/jpeg",
        "image/png",
        "application/pdf",
    ]

    # Forensic analysis defaults
    ela_jpeg_qualities: list[int] = [90, 95]
    ela_amplification_factor: float = 12.0
    ela_mean_error_threshold: float = 4.0
    ela_peak_anomaly_threshold: float = 2.0
    ela_anomaly_coverage_threshold: float = 0.035
    ela_localized_hotspot_threshold: int = 3
    ela_pixel_threshold: float = 18.0

    # Deep learning inference
    enable_transformers_inference: bool = True
    feature_extractor_model: str = "efficientnet_b0_imagenet1k"

    # Risk engine weights and thresholds
    risk_weight_metadata: int = 25
    risk_weight_ela: int = 30
    risk_weight_layout: int = 20
    risk_weight_deep_learning: int = 25
    risk_weight_authenticity: int = 20
    dl_anomaly_threshold: float = 0.62
    dl_anomaly_partial_threshold: float = 0.48
    authenticity_threshold: float = 0.58
    risk_level_low_max: int = 29
    risk_level_medium_max: int = 65


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    settings = Settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.heatmap_dir.mkdir(parents=True, exist_ok=True)
    settings.temp_dir.mkdir(parents=True, exist_ok=True)
    return settings
