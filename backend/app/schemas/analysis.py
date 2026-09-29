"""API schemas for document analysis responses."""

from typing import Any

from pydantic import BaseModel, Field


class AnalysisResult(BaseModel):
    """Frontend-compatible analysis payload."""

    risk_score: int = Field(..., ge=0, le=100)
    risk_level: str
    reasons: list[str]
    original_image_url: str
    heatmap_image_url: str
    extracted_fields: dict[str, Any] = Field(default_factory=dict)
    anomaly_score: float = Field(..., ge=0.0, le=1.0)
    inference_method: str
    component_scores: dict[str, int] = Field(default_factory=dict)
    status: str = Field(default="success")
