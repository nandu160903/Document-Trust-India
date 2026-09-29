"""Optional UVDoc correction for severe geometric distortion."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from app.core.config import Settings, get_settings


class UVDocCorrectionService:
    """
    Optional UVDoc unwarping module.

    Disabled by default to keep deployment lightweight.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def enabled(self) -> bool:
        return self.settings.uvdoc_enabled and self.settings.uvdoc_model_dir.exists()

    def should_apply(self, image_bgr: np.ndarray, corner_confidence: float) -> bool:
        if not self.enabled:
            return False
        if corner_confidence >= 0.85:
            return False
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = float(np.mean(edges > 0))
        return edge_density > 0.18

    def unwarp(self, image_bgr: np.ndarray) -> np.ndarray:
        if not self.enabled:
            return image_bgr

        model_files = list(self.settings.uvdoc_model_dir.glob("*.onnx"))
        if not model_files:
            raise FileNotFoundError(
                "UVDoc enabled but no ONNX model found in models/uvdoc/."
            )

        from app.utils.model_runtime import create_runtime

        runtime = create_runtime(
            model_files[0],
            backend=self.settings.onnx_inference_backend,
            providers=self.settings.onnx_execution_providers or None,
        )
        resized = cv2.resize(image_bgr, (512, 512), interpolation=cv2.INTER_LINEAR)
        tensor = np.transpose(resized.astype(np.float32) / 255.0, (2, 0, 1))[None, ...]
        output = runtime.infer(tensor=tensor)[0]
        corrected = np.transpose(output[0], (1, 2, 0))
        corrected = np.clip(corrected * 255.0, 0, 255).astype(np.uint8)
        return cv2.resize(corrected, (image_bgr.shape[1], image_bgr.shape[0]))
