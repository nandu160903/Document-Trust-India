"""End-to-end document forensic analysis pipeline."""

from __future__ import annotations

from pathlib import Path

from app.core.config import Settings, get_settings
from app.schemas.analysis import AnalysisResult
from app.services.risk_engine import RiskEngine


class DocumentAnalyzerPipeline:
    """Orchestrates forensic services and risk scoring for one document."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.risk_engine = RiskEngine(settings=self.settings)

    def run(
        self,
        file_path: str | Path,
        *,
        stored_filename: str | None = None,
    ) -> AnalysisResult:
        path = Path(file_path)
        assessment = self.risk_engine.analyze_document(path)

        upload_name = stored_filename or path.name
        original_url = self._build_upload_url(upload_name)
        heatmap_url = self._build_heatmap_url(Path(assessment["heatmap_path"]))

        return AnalysisResult(
            risk_score=assessment["risk_score"],
            risk_level=assessment["risk_level"],
            reasons=assessment["reasons"],
            original_image_url=original_url,
            heatmap_image_url=heatmap_url,
            extracted_fields=assessment["extracted_fields"],
            anomaly_score=assessment["anomaly_score"],
            inference_method=assessment["inference_method"],
            component_scores=assessment["component_scores"],
        )

    def _build_upload_url(self, filename: str) -> str:
        return f"{self.settings.static_uploads_prefix}/{filename}"

    def _build_heatmap_url(self, heatmap_path: Path) -> str:
        return f"{self.settings.static_heatmaps_prefix}/{heatmap_path.name}"
