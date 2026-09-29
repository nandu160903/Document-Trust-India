"""Perspective correction for detected document quadrilaterals."""

from __future__ import annotations

import time
import uuid
from pathlib import Path

import cv2
import numpy as np

from app.core.config import Settings, get_settings
from app.schemas.document_models import PerspectiveResult


class PerspectiveCorrectionService:
    """Warp detected document corners into a normalized rectangular image."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def rectify(
        self,
        image_bgr: np.ndarray,
        corners: dict[str, list[float]],
        *,
        output_path: Path | None = None,
    ) -> PerspectiveResult:
        start = time.perf_counter()
        src = np.array(
            [
                corners["top_left"],
                corners["top_right"],
                corners["bottom_right"],
                corners["bottom_left"],
            ],
            dtype=np.float32,
        )

        width_a = np.linalg.norm(src[2] - src[3])
        width_b = np.linalg.norm(src[1] - src[0])
        height_a = np.linalg.norm(src[1] - src[2])
        height_b = np.linalg.norm(src[0] - src[3])

        max_width = int(max(width_a, width_b))
        max_height = int(max(height_a, height_b))
        max_width = max(max_width, 320)
        max_height = max(max_height, 240)

        dst = np.array(
            [
                [0, 0],
                [max_width - 1, 0],
                [max_width - 1, max_height - 1],
                [0, max_height - 1],
            ],
            dtype=np.float32,
        )

        matrix = cv2.getPerspectiveTransform(src, dst)
        rectified = cv2.warpPerspective(image_bgr, matrix, (max_width, max_height))

        destination = output_path or (
            self.settings.rectified_output_dir / f"{uuid.uuid4().hex}_rectified.png"
        )
        cv2.imwrite(str(destination), rectified)

        return PerspectiveResult(
            rectified_path=str(destination.resolve()),
            width=max_width,
            height=max_height,
            runtime_ms=(time.perf_counter() - start) * 1000,
        )
