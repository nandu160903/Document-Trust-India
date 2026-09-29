"""Document corner extraction from segmentation masks."""

from __future__ import annotations

import time

import cv2
import numpy as np

from app.utils.geometry import order_corners, refine_corners, validate_quadrilateral


class CornerDetectorService:
    """Extract and validate four document corners from a binary mask."""

    def extract(
        self,
        mask: np.ndarray,
        image_bgr: np.ndarray,
    ) -> tuple[dict[str, list[float]] | None, float]:
        start = time.perf_counter()
        binary = (mask > 0).astype(np.uint8)
        cleaned = self._remove_small_components(binary)

        contours, _ = cv2.findContours(
            cleaned,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        if not contours:
            return None, (time.perf_counter() - start) * 1000

        contour = max(contours, key=cv2.contourArea)
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        if len(approx) != 4:
            rect = cv2.minAreaRect(contour)
            box = cv2.boxPoints(rect)
            corners = order_corners(box.astype(np.float32))
        else:
            corners = order_corners(approx.reshape(4, 2).astype(np.float32))

        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        corners = refine_corners(gray, corners)

        if not validate_quadrilateral(corners, image_bgr.shape):
            return None, (time.perf_counter() - start) * 1000

        ordered = {
            "top_left": corners[0].tolist(),
            "top_right": corners[1].tolist(),
            "bottom_right": corners[2].tolist(),
            "bottom_left": corners[3].tolist(),
        }
        return ordered, (time.perf_counter() - start) * 1000

    @staticmethod
    def _remove_small_components(binary: np.ndarray, min_area: int = 500) -> np.ndarray:
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, 8)
        cleaned = np.zeros_like(binary)
        for label in range(1, num_labels):
            if stats[label, cv2.CC_STAT_AREA] >= min_area:
                cleaned[labels == label] = 1
        return cleaned
