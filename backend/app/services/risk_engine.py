"""Risk scoring engine aggregating forensic and ML signals."""

from __future__ import annotations

from pathlib import Path

from app.core.config import Settings, get_settings
from app.schemas.forensics import (
    AuthenticityAnalysisResult,
    ELAAnalysisResult,
    MetadataAnalysisResult,
    ModelInferenceResult,
    OCRLayoutResult,
    RiskAssessmentResult,
)
from app.services.authenticity_analyzer import AuthenticityAnalyzer
from app.services.ela_detector import ELADetector
from app.services.forensics_utils import load_document_context
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
        self.authenticity_analyzer = AuthenticityAnalyzer()
        self.model_inference = ModelInferenceService(settings=self.settings)

    def assess(
        self,
        metadata: MetadataAnalysisResult,
        ela: ELAAnalysisResult,
        ocr: OCRLayoutResult,
        inference: ModelInferenceResult,
        authenticity: AuthenticityAnalysisResult,
    ) -> RiskAssessmentResult:
        component_scores: dict[str, int] = {
            "metadata": 0,
            "ela": 0,
            "layout": 0,
            "deep_learning": 0,
            "authenticity": 0,
        }
        reasons: list[str] = []

        if metadata["has_manipulation_tools"]:
            component_scores["metadata"] = self.settings.risk_weight_metadata
            reasons.append(
                f"Software manipulation signature detected: {metadata['software_tag']}"
            )

        if self._ela_threshold_exceeded(ela, authenticity["authenticity_score"]):
            component_scores["ela"] = self.settings.risk_weight_ela
            coverage = float(ela.get("anomaly_coverage_ratio", 0.0))
            if coverage >= self.settings.ela_anomaly_coverage_threshold:
                reasons.append(
                    "Localized compression anomalies detected via multi-quality ELA "
                    f"(coverage {coverage:.1%})."
                )
            else:
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

        component_scores["deep_learning"] = self._deep_learning_component_score(
            inference["anomaly_score"]
        )
        if component_scores["deep_learning"] > 0:
            reasons.append(
                "Deep learning patch ensemble flagged statistical outliers "
                f"(confidence {inference['anomaly_score']:.2f})."
            )

        if authenticity["authenticity_score"] < self.settings.authenticity_threshold:
            component_scores["authenticity"] = self.settings.risk_weight_authenticity
            for flag in authenticity["flags"][:2]:
                reasons.append(flag)
            if not authenticity["flags"]:
                reasons.append(
                    "Document authenticity consistency score below trusted threshold."
                )

        for flag in metadata["flags"]:
            if flag not in reasons and "Editing software signature" not in flag:
                reasons.append(flag)

        risk_score = int(min(100, sum(component_scores.values())))
        risk_level = self._categorize_risk(risk_score)
        authenticity_percentage, risk_percentage = self._compute_user_percentages(
            authenticity=authenticity,
            risk_score=risk_score,
            anomaly_score=inference["anomaly_score"],
        )

        if risk_score == 0:
            reasons = [
                "Document integrity indicators are consistent with an authentic capture pipeline.",
                f"Authenticity: {authenticity_percentage}% · Risk: {risk_percentage}%.",
            ]

        return {
            "risk_score": risk_score,
            "risk_percentage": risk_percentage,
            "authenticity_percentage": authenticity_percentage,
            "risk_level": risk_level,
            "reasons": reasons,
            "anomaly_score": inference["anomaly_score"],
            "authenticity_score": authenticity["authenticity_score"],
            "inference_method": inference["method"],
            "component_scores": component_scores,
            "extracted_fields": self._build_extracted_fields(ocr, authenticity),
        }

    def analyze_document(self, file_path: str | Path) -> RiskAssessmentResult:
        """Run full forensic pipeline with single image load for efficiency."""
        context = load_document_context(file_path)

        metadata = self.metadata_analyzer.analyze(context.path)
        ela = self.ela_detector.analyze(context=context)
        ocr = self.ocr_analyzer.analyze(context.path)
        authenticity = self.authenticity_analyzer.analyze(context=context)
        inference = self.model_inference.predict(context=context)

        assessment = self.assess(metadata, ela, ocr, inference, authenticity)
        assessment["heatmap_path"] = ela["heatmap_path"]
        assessment["metadata"] = metadata
        assessment["ela"] = ela
        assessment["ocr_layout"] = ocr
        assessment["inference"] = inference
        assessment["authenticity"] = authenticity
        return assessment

    def _ela_threshold_exceeded(
        self,
        ela: ELAAnalysisResult,
        authenticity_score: float,
    ) -> bool:
        coverage = float(ela.get("anomaly_coverage_ratio", 0.0))
        hotspots = int(ela.get("localized_hotspots", 0))
        peak = float(ela["peak_anomaly_ratio"])
        mean = float(ela["mean_error"])

        if mean < 1.0:
            return False

        ela_signal = (
            0.4 * min(1.0, coverage / 0.12)
            + 0.3 * min(1.0, peak / 5.0)
            + 0.3 * min(1.0, hotspots / 10.0)
        )
        trigger_threshold = 0.55
        if authenticity_score >= 0.75:
            trigger_threshold = 0.78

        return ela_signal >= trigger_threshold

    def _deep_learning_component_score(self, anomaly_score: float) -> int:
        if anomaly_score >= self.settings.dl_anomaly_threshold:
            return self.settings.risk_weight_deep_learning
        if anomaly_score >= self.settings.dl_anomaly_partial_threshold:
            return max(10, self.settings.risk_weight_deep_learning // 2)
        return 0

    def _meaningful_layout_flags(self, flags: list[str]) -> list[str]:
        return [flag for flag in flags if flag not in self.BENIGN_LAYOUT_MESSAGES]

    def _categorize_risk(self, risk_score: int) -> str:
        if risk_score < self.settings.risk_level_low_max:
            return "LOW"
        if risk_score <= self.settings.risk_level_medium_max:
            return "MEDIUM"
        return "HIGH"

    @staticmethod
    def _compute_user_percentages(
        authenticity: AuthenticityAnalysisResult,
        risk_score: int,
        anomaly_score: float,
    ) -> tuple[int, int]:
        """
        Derive user-facing percentages:
        - authenticity_percentage: how genuine the document appears (higher is better)
        - risk_percentage: tampering/fraud indicator strength (higher is worse)
        """
        risk_percentage = int(max(0, min(100, risk_score)))
        forensic_pct = float(authenticity["authenticity_score"]) * 100.0
        inverse_risk_pct = 100.0 - risk_percentage
        inverse_anomaly_pct = (1.0 - anomaly_score) * 100.0

        blended = (
            0.50 * forensic_pct
            + 0.35 * inverse_risk_pct
            + 0.15 * inverse_anomaly_pct
        )
        authenticity_percentage = int(round(max(0.0, min(100.0, blended))))
        return authenticity_percentage, risk_percentage

    @staticmethod
    def _build_extracted_fields(
        ocr: OCRLayoutResult,
        authenticity: AuthenticityAnalysisResult,
    ) -> dict[str, str | float]:
        fields: dict[str, str | float] = {}
        for index, block in enumerate(ocr["extracted_text"][:10], start=1):
            fields[f"text_block_{index}"] = block["text"]
            fields[f"text_block_{index}_confidence"] = block["confidence"]
        return fields
