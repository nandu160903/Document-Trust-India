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
from app.services.forensics_utils import load_document_rgb


class ELADetector:
    """
    Detect localized compression anomalies via Error Level Analysis.

    The image is re-compressed at a fixed JPEG quality, differenced against
    the original, amplified, and saved as a heatmap artifact.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        jpeg_quality: int = 92,
        amplification_factor: float = 10.0,
        anomaly_threshold: float = 30.0,
    ) -> None:
        self.settings = settings or get_settings()
        self.jpeg_quality = jpeg_quality
        self.amplification_factor = amplification_factor
        self.anomaly_threshold = anomaly_threshold
        self.settings.heatmap_dir.mkdir(parents=True, exist_ok=True)

    def analyze(
        self,
        file_path: str | Path,
        artifact_name: str | None = None,
    ) -> ELAAnalysisResult:
        path = Path(file_path)
        image = load_document_rgb(path)

        original = np.asarray(image, dtype=np.float32)
        recompressed = self._recompress_jpeg(image)
        difference = np.abs(original - recompressed)
        amplified = np.clip(difference * self.amplification_factor, 0, 255).astype(
            np.uint8
        )

        gray = cv2.cvtColor(amplified, cv2.COLOR_RGB2GRAY)
        mean_error = float(np.mean(gray))
        peak_value = float(np.max(gray))
        peak_anomaly_ratio = float(
            peak_value / (mean_error + 1e-6) if mean_error > 0 else peak_value
        )

        heatmap = cv2.applyColorMap(gray, cv2.COLORMAP_JET)
        overlay = cv2.addWeighted(
            cv2.cvtColor(original.astype(np.uint8), cv2.COLOR_RGB2BGR),
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
            "peak_anomaly_ratio": round(peak_anomaly_ratio, 4),
            "heatmap_path": str(heatmap_path.resolve()),
        }

    def _recompress_jpeg(self, image: Image.Image) -> np.ndarray:
        buffer = io.BytesIO()
        image.save(
            buffer,
            format="JPEG",
            quality=self.jpeg_quality,
            optimize=True,
        )
        buffer.seek(0)
        recompressed = Image.open(buffer).convert("RGB")
        return np.asarray(recompressed, dtype=np.float32)
