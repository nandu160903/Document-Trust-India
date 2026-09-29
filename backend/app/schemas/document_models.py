"""Schemas for document CV model pipeline outputs."""

from typing import Any

from pydantic import BaseModel, Field


class Point(BaseModel):
    x: float
    y: float


class DocumentDetectionResult(BaseModel):
    detected: bool
    confidence: float = 0.0
    bbox: list[float] = Field(default_factory=list)
    mask_path: str | None = None
    corners: dict[str, list[float]] | None = None
    model_version: str
    runtime_ms: float = 0.0


class PerspectiveResult(BaseModel):
    rectified_path: str | None = None
    width: int = 0
    height: int = 0
    runtime_ms: float = 0.0


class OrientationResult(BaseModel):
    angle: int = 0
    confidence: float = 0.0
    model_version: str
    runtime_ms: float = 0.0


class DocumentTypeCandidate(BaseModel):
    type: str
    confidence: float


class DocumentClassificationResult(BaseModel):
    document_type: str
    confidence: float
    top_candidates: list[DocumentTypeCandidate] = Field(default_factory=list)
    model_version: str
    runtime_ms: float = 0.0


class OCRTextElement(BaseModel):
    text: str
    confidence: float
    bbox: list[list[float]]


class OCRResult(BaseModel):
    elements: list[OCRTextElement] = Field(default_factory=list)
    engine_version: str
    runtime_ms: float = 0.0


class MilestoneOnePipelineResult(BaseModel):
    request_id: str
    document_detection: DocumentDetectionResult
    perspective: PerspectiveResult
    model_versions: dict[str, str] = Field(default_factory=dict)
    timings_ms: dict[str, float] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
