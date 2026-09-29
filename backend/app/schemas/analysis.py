"""API schemas for document analysis responses."""

from typing import Any

from pydantic import BaseModel, Field


class AnalysisResult(BaseModel):
    """Frontend-compatible analysis payload."""

    authenticity_percentage: int = Field(
        ...,
        ge=0,
        le=100,
        description="How likely the document is genuine (higher is better).",
    )
    risk_percentage: int = Field(
        ...,
        ge=0,
        le=100,
        description="Tampering or fraud indicator strength (higher is worse).",
    )
    risk_level: str
    reasons: list[str]
    original_image_url: str
    heatmap_image_url: str
    extracted_fields: dict[str, Any] = Field(default_factory=dict)
    anomaly_score: float = Field(..., ge=0.0, le=1.0)
    authenticity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Raw forensic authenticity score (0–1).",
    )
    inference_method: str
    component_scores: dict[str, int] = Field(default_factory=dict)
    status: str = Field(default="success")
    # Backward-compatible alias for older clients
    risk_score: int = Field(..., ge=0, le=100)
