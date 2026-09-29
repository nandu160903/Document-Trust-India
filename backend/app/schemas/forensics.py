"""Typed result schemas for forensic analysis services."""

from typing import TypedDict


class MetadataAnalysisResult(TypedDict):
    has_manipulation_tools: bool
    software_tag: str
    flags: list[str]


class ELAAnalysisResult(TypedDict):
    mean_error: float
    peak_anomaly_ratio: float
    heatmap_path: str
    std_error: float
    anomaly_coverage_ratio: float
    localized_hotspots: int


class AuthenticityAnalysisResult(TypedDict):
    authenticity_score: float
    flags: list[str]
    details: dict[str, float]


class ExtractedTextBlock(TypedDict):
    text: str
    confidence: float
    bbox: list[list[float]]
    aspect_ratio: float
    baseline_y: float


class OCRLayoutResult(TypedDict):
    extracted_text: list[ExtractedTextBlock]
    layout_inconsistencies: list[str]


class ModelInferenceResult(TypedDict):
    anomaly_score: float
    method: str
    model_id: str
    details: dict[str, float]


class RiskAssessmentResult(TypedDict, total=False):
    risk_score: int
    risk_percentage: int
    authenticity_percentage: int
    risk_level: str
    reasons: list[str]
    anomaly_score: float
    authenticity_score: float
    inference_method: str
    component_scores: dict[str, int]
    extracted_fields: dict[str, str | float]
    heatmap_path: str
    metadata: MetadataAnalysisResult
    ela: ELAAnalysisResult
    ocr_layout: OCRLayoutResult
    authenticity: AuthenticityAnalysisResult
    inference: ModelInferenceResult
