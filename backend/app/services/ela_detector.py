"""Error Level Analysis (ELA) forgery detection service."""

from __future__ import annotations

import io
import uuid
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from app.core.config import Settings, get_settings
from app.schemas.forensics import ELAAnalysisResult
from app.services.forensics_utils import DocumentImageContext, load_document_context


class ELADetector:
    """
    Detect localized compression anomalies via multi-quality Error Level Analysis.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.settings.heatmap_dir.mkdir(parents=True, exist_ok=True)

    def analyze(
        self,
        file_path: str | Path | None = None,
        *,
        context: DocumentImageContext | None = None,
        artifact_name: str | None = None,
    ) -> ELAAnalysisResult:
        ctx = context or load_document_context(file_path)  # type: ignore[arg-type]
        image = ctx.pil_image

        error_maps: list[np.ndarray] = []
        for quality in self.settings.ela_jpeg_qualities:
            original = np.asarray(image, dtype=np.float32)
            recompressed = self._recompress_jpeg(image, quality=quality)
            difference = np.abs(original - recompressed)
            amplified = np.clip(
                difference * self.settings.ela_amplification_factor,
                0,
                255,
            ).astype(np.uint8)
            error_maps.append(cv2.cvtColor(amplified, cv2.COLOR_RGB2GRAY))

        gray = np.max(np.stack(error_maps, axis=0), axis=0)
        mean_error = float(np.mean(gray))
        std_error = float(np.std(gray))
        peak_value = float(np.max(gray))
        adaptive_threshold = mean_error + (1.8 * std_error)
        anomaly_mask = gray >= max(adaptive_threshold, self.settings.ela_pixel_threshold)
        anomaly_coverage_ratio = float(np.mean(anomaly_mask))
        peak_anomaly_ratio = float(
            peak_value / (mean_error + 1e-6) if mean_error > 0 else peak_value
        )
        localized_hotspots = int(np.sum(anomaly_mask) // max(1, (gray.shape[0] * gray.shape[1]) // 400))

        heatmap = cv2.applyColorMap(gray, cv2.COLORMAP_JET)
        overlay = cv2.addWeighted(
            cv2.cvtColor(ctx.rgb, cv2.COLOR_RGB2BGR),
            0.55,
            heatmap,
            0.45,
            0,
        )

        filename = artifact_name or f"{uuid.uuid4().hex}_ela.png"
        heatmap_path = self.settings.heatmap_dir / filename
        cv2.imwrite(str(heatmap_path), overlay)

        return {
            "mean_error": round(mean_error, 4),
            "std_error": round(std_error, 4),
            "peak_anomaly_ratio": round(peak_anomaly_ratio, 4),
            "anomaly_coverage_ratio": round(anomaly_coverage_ratio, 4),
            "localized_hotspots": localized_hotspots,
            "heatmap_path": str(heatmap_path.resolve()),
        }

    @staticmethod
    def _recompress_jpeg(image: Image.Image, *, quality: int) -> np.ndarray:
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=quality, optimize=True)
        buffer.seek(0)
        recompressed = Image.open(buffer).convert("RGB")
        return np.asarray(recompressed, dtype=np.float32)
