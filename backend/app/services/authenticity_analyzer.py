"""Advanced document authenticity and tamper-consistency analysis."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from app.schemas.forensics import AuthenticityAnalysisResult
from app.services.forensics_utils import DocumentImageContext, load_document_context


class AuthenticityAnalyzer:
    """
    Multi-signal authenticity scoring using noise, illumination, texture,
    frequency, and duplicate-region heuristics.
    """

    GRID_SIZE = 8

    def analyze(
        self,
        file_path: str | Path | None = None,
        *,
        context: DocumentImageContext | None = None,
    ) -> AuthenticityAnalysisResult:
        ctx = context or load_document_context(file_path)  # type: ignore[arg-type]
        gray = ctx.gray
        metrics = self._patch_metrics(gray)

        noise_consistency = self._consistency_score(metrics["noise"])
        illumination_consistency = self._consistency_score(metrics["illumination"])
        texture_consistency = self._consistency_score(metrics["texture"])
        frequency_consistency = self._consistency_score(metrics["frequency"])
        duplicate_penalty = self._duplicate_region_penalty(gray)

        authenticity_score = float(
            np.clip(
                0.30 * noise_consistency
                + 0.25 * illumination_consistency
                + 0.20 * texture_consistency
                + 0.15 * frequency_consistency
                + 0.10 * (1.0 - duplicate_penalty),
                0.0,
                1.0,
            )
        )

        flags: list[str] = []
        if noise_consistency < 0.55:
            flags.append(
                "Inconsistent noise residuals detected across document regions."
            )
        if illumination_consistency < 0.55:
            flags.append(
                "Uneven illumination patterns suggest localized image manipulation."
            )
        if texture_consistency < 0.55:
            flags.append(
                "Texture statistics vary abnormally between document segments."
            )
        if frequency_consistency < 0.55:
            flags.append(
                "Frequency-domain artifacts indicate possible resampling or splicing."
            )
        if duplicate_penalty > 0.45:
            flags.append(
                "Repeated structural patterns detected (possible copy-move forgery)."
            )

        return {
            "authenticity_score": round(authenticity_score, 4),
            "flags": flags,
            "details": {
                "noise_consistency": round(noise_consistency, 4),
                "illumination_consistency": round(illumination_consistency, 4),
                "texture_consistency": round(texture_consistency, 4),
                "frequency_consistency": round(frequency_consistency, 4),
                "duplicate_region_penalty": round(duplicate_penalty, 4),
            },
        }

    def _patch_metrics(self, gray: np.ndarray) -> dict[str, list[float]]:
        h, w = gray.shape
        patch_h = max(1, h // self.GRID_SIZE)
        patch_w = max(1, w // self.GRID_SIZE)

        noise_values: list[float] = []
        illumination_values: list[float] = []
        texture_values: list[float] = []
        frequency_values: list[float] = []

        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        for row in range(self.GRID_SIZE):
            for col in range(self.GRID_SIZE):
                y1 = row * patch_h
                x1 = col * patch_w
                y2 = h if row == self.GRID_SIZE - 1 else (row + 1) * patch_h
                x2 = w if col == self.GRID_SIZE - 1 else (col + 1) * patch_w
                patch = gray[y1:y2, x1:x2]
                if patch.size == 0:
                    continue

                residual = patch.astype(np.float32) - blurred[y1:y2, x1:x2]
                noise_values.append(float(np.std(residual)))
                illumination_values.append(float(np.mean(patch)))
                texture_values.append(float(cv2.Laplacian(patch, cv2.CV_64F).var()))

                f_patch = np.fft.fftshift(np.fft.fft2(patch.astype(np.float32)))
                magnitude = np.log1p(np.abs(f_patch))
                frequency_values.append(float(np.mean(magnitude)))

        return {
            "noise": noise_values,
            "illumination": illumination_values,
            "texture": texture_values,
            "frequency": frequency_values,
        }

    @staticmethod
    def _consistency_score(values: list[float]) -> float:
        if len(values) < 2:
            return 1.0
        array = np.asarray(values, dtype=np.float32)
        mean = float(np.mean(array))
        std = float(np.std(array))
        if mean <= 1e-6:
            return float(np.clip(1.0 - std / 32.0, 0.0, 1.0))
        coefficient_of_variation = std / (mean + 1e-6)
        return float(np.clip(1.0 - coefficient_of_variation * 1.8, 0.0, 1.0))

    def _duplicate_region_penalty(self, gray: np.ndarray) -> float:
        """Detect repeated structures using ORB keypoint self-matching."""
        resized = self._resize_max_side(gray, 640)
        orb = cv2.ORB_create(nfeatures=900)
        keypoints, descriptors = orb.detectAndCompute(resized, None)
        if descriptors is None or len(keypoints) < 12:
            return 0.0

        matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        matches = matcher.knnMatch(descriptors, descriptors, k=2)

        suspicious = 0
        valid = 0
        for match_pair in matches:
            if len(match_pair) < 2:
                continue
            first, second = match_pair
            if first.trainIdx == first.queryIdx:
                continue
            if first.distance >= 32 or second.distance <= 0:
                continue
            if first.distance / (second.distance + 1e-6) > 0.75:
                continue

            pt_a = keypoints[first.queryIdx].pt
            pt_b = keypoints[first.trainIdx].pt
            distance = float(np.hypot(pt_a[0] - pt_b[0], pt_a[1] - pt_b[1]))
            if distance < 36:
                continue

            valid += 1
            if distance > 90:
                suspicious += 1

        if valid == 0:
            return 0.0
        return float(np.clip(suspicious / valid, 0.0, 1.0))

    @staticmethod
    def _resize_max_side(gray: np.ndarray, max_side: int) -> np.ndarray:
        h, w = gray.shape
        scale = max_side / max(h, w)
        if scale >= 1.0:
            return gray
        return cv2.resize(
            gray,
            (int(w * scale), int(h * scale)),
            interpolation=cv2.INTER_AREA,
        )
