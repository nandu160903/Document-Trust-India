"""Risk scoring engine aggregating forensic and ML signals."""

from __future__ import annotations

from pathlib import Path

from app.core.config import Settings, get_settings
from app.schemas.forensics import (
    ELAAnalysisResult,
    MetadataAnalysisResult,
    ModelInferenceResult,
    OCRLayoutResult,
    RiskAssessmentResult,
)
from app.services.ela_detector import ELADetector
from app.services.metadata_analyzer import MetadataAnalyzer
from app.services.model_inference import ModelInferenceService
from app.services.ocr_layout import OCRLayoutAnalyzer


class RiskEngine:
    """Aggregate forensic outputs into a normalized risk score and narrative."""

    BENIGN_LAYOUT_MESSAGES = {
        "No OCR text detected in document.",
    }

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.metadata_analyzer = MetadataAnalyzer()
        self.ela_detector = ELADetector(settings=self.settings)
        self.ocr_analyzer = OCRLayoutAnalyzer()
        self.model_inference = ModelInferenceService(settings=self.settings)

    def assess(
        self,
        metadata: MetadataAnalysisResult,
        ela: ELAAnalysisResult,
        ocr: OCRLayoutResult,
        inference: ModelInferenceResult,
    ) -> RiskAssessmentResult:
        component_scores: dict[str, int] = {
            "metadata": 0,
            "ela": 0,
            "layout": 0,
            "deep_learning": 0,
        }
        reasons: list[str] = []

        if metadata["has_manipulation_tools"]:
            component_scores["metadata"] = self.settings.risk_weight_metadata
            software = metadata["software_tag"]
            reasons.append(
                f"Software manipulation signature detected: {software}"
            )

        if self._ela_threshold_exceeded(ela):
            component_scores["ela"] = self.settings.risk_weight_ela
            reasons.append("Localized compression anomalies detected via ELA")

        layout_flags = self._meaningful_layout_flags(ocr["layout_inconsistencies"])
        if layout_flags:
            component_scores["layout"] = self.settings.risk_weight_layout
            for flag in layout_flags[:3]:
                reasons.append(flag)
            if len(layout_flags) > 3:
                reasons.append(
                    f"{len(layout_flags) - 3} additional layout inconsistency signals detected."
                )

        if inference["anomaly_score"] > self.settings.dl_anomaly_threshold:
            component_scores["deep_learning"] = self.settings.risk_weight_deep_learning
            reasons.append(
                "Deep learning anomaly confidence exceeded threshold "
                f"({inference['anomaly_score']:.2f})."
            )

        for flag in metadata["flags"]:
            if flag not in reasons and "Editing software signature" not in flag:
                reasons.append(flag)

        risk_score = int(min(100, sum(component_scores.values())))
        risk_level = self._categorize_risk(risk_score)

        if not reasons:
            reasons.append("No significant tampering indicators detected.")

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "reasons": reasons,
            "anomaly_score": inference["anomaly_score"],
            "inference_method": inference["method"],
            "component_scores": component_scores,
            "extracted_fields": self._build_extracted_fields(ocr),
        }

    def analyze_document(self, file_path: str | Path) -> RiskAssessmentResult:
        """Run Module 1 + Module 2 pipeline and return risk assessment."""
        path = Path(file_path)

        metadata = self.metadata_analyzer.analyze(path)
        ela = self.ela_detector.analyze(path)
        ocr = self.ocr_analyzer.analyze(path)
        inference = self.model_inference.predict(path)

        assessment = self.assess(metadata, ela, ocr, inference)
        assessment["heatmap_path"] = ela["heatmap_path"]
        assessment["metadata"] = metadata
        assessment["ela"] = ela
        assessment["ocr_layout"] = ocr
        assessment["inference"] = inference
        return assessment

    def _ela_threshold_exceeded(self, ela: ELAAnalysisResult) -> bool:
        return (
            ela["mean_error"] >= self.settings.ela_mean_error_threshold
            or ela["peak_anomaly_ratio"] >= self.settings.ela_peak_anomaly_threshold
        )

    def _meaningful_layout_flags(self, flags: list[str]) -> list[str]:
        return [
            flag
            for flag in flags
            if flag not in self.BENIGN_LAYOUT_MESSAGES
        ]

    def _categorize_risk(self, risk_score: int) -> str:
        if risk_score < self.settings.risk_level_low_max:
            return "LOW"
        if risk_score <= self.settings.risk_level_medium_max:
            return "MEDIUM"
        return "HIGH"

    @staticmethod
    def _build_extracted_fields(ocr: OCRLayoutResult) -> dict[str, str | float]:
        fields: dict[str, str | float] = {}
        for index, block in enumerate(ocr["extracted_text"][:10], start=1):
            fields[f"text_block_{index}"] = block["text"]
            fields[f"text_block_{index}_confidence"] = block["confidence"]
        return fields
