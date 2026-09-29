"""Deep learning and forensic ensemble inference for document tampering."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

import cv2
import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0
from torchvision.transforms import functional as tf

from app.core.config import Settings, get_settings
from app.schemas.forensics import ModelInferenceResult
from app.services.forensics_utils import DocumentImageContext, load_document_context

logger = logging.getLogger(__name__)

InferenceMethod = Literal["efficientnet_patch_ensemble", "heuristic_cv"]


@dataclass
class _EfficientNetRuntime:
    model: nn.Module
    device: str


class ModelInferenceService:
    """
    Ensemble tamper inference using EfficientNet patch outlier scoring
    plus classical CV forensic features.
    """

    PATCH_GRID = 4

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._runtime: _EfficientNetRuntime | None = None
        self._runtime_failed = False

    def predict(
        self,
        file_path: str | Path | None = None,
        *,
        context: DocumentImageContext | None = None,
    ) -> ModelInferenceResult:
        ctx = context or load_document_context(file_path)  # type: ignore[arg-type]

        if self.settings.enable_transformers_inference and not self._runtime_failed:
            try:
                score, details = self._predict_with_efficientnet(ctx)
                return {
                    "anomaly_score": round(score, 4),
                    "method": "efficientnet_patch_ensemble",
                    "model_id": self.settings.feature_extractor_model,
                    "details": details,
                }
            except Exception as exc:
                self._runtime_failed = True
                logger.warning(
                    "EfficientNet inference unavailable, using heuristic fallback: %s",
                    exc,
                )

        score, details = self._predict_with_heuristics(ctx.bgr)
        return {
            "anomaly_score": round(score, 4),
            "method": "heuristic_cv",
            "model_id": "opencv-heuristic-v2",
            "details": details,
        }

    def _predict_with_efficientnet(
        self,
        context: DocumentImageContext,
    ) -> tuple[float, dict[str, float]]:
        runtime = self._get_runtime()
        patches = self._extract_patches(context.pil_image)
        if not patches:
            raise RuntimeError("Unable to extract image patches for inference.")

        batch = torch.stack(
            [self._preprocess_patch(patch) for patch in patches]
        ).to(runtime.device)

        with torch.no_grad():
            features = runtime.model(batch).detach().cpu().numpy()

        norms = np.linalg.norm(features, axis=1)
        median = float(np.median(norms))
        mad = float(np.median(np.abs(norms - median)) + 1e-6)
        z_scores = (norms - median) / (1.4826 * mad)
        patch_outlier = float(np.clip(np.max(z_scores) / 4.0, 0.0, 1.0))

        forensic_score, forensic_details = self._predict_with_heuristics(context.bgr)
        combined = float(
            np.clip(
                0.65 * patch_outlier + 0.35 * forensic_score,
                0.0,
                1.0,
            )
        )

        details = {
            "patch_outlier_score": round(patch_outlier, 4),
            "patch_z_max": round(float(np.max(z_scores)), 4),
            **forensic_details,
        }
        return combined, details

    def _get_runtime(self) -> _EfficientNetRuntime:
        if self._runtime is not None:
            return self._runtime

        device = "cuda" if torch.cuda.is_available() else "cpu"
        backbone = efficientnet_b0(weights=EfficientNet_B0_Weights.IMAGENET1K_V1)
        backbone.classifier = nn.Identity()
        backbone.eval()
        backbone.to(device)
        self._runtime = _EfficientNetRuntime(model=backbone, device=device)
        return self._runtime

    def _extract_patches(self, image: Image.Image) -> list[Image.Image]:
        width, height = image.size
        patch_w = max(1, width // self.PATCH_GRID)
        patch_h = max(1, height // self.PATCH_GRID)
        patches: list[Image.Image] = []

        for row in range(self.PATCH_GRID):
            for col in range(self.PATCH_GRID):
                left = col * patch_w
                top = row * patch_h
                right = width if col == self.PATCH_GRID - 1 else (col + 1) * patch_w
                bottom = height if row == self.PATCH_GRID - 1 else (row + 1) * patch_h
                patch = image.crop((left, top, right, bottom))
                if patch.width > 8 and patch.height > 8:
                    patches.append(patch.resize((224, 224), Image.Resampling.BILINEAR))
        return patches

    @staticmethod
    def _preprocess_patch(patch: Image.Image) -> torch.Tensor:
        tensor = tf.to_tensor(patch)
        return tf.normalize(
            tensor,
            mean=(0.485, 0.456, 0.406),
            std=(0.229, 0.224, 0.225),
        )

    def _predict_with_heuristics(self, image_bgr: np.ndarray) -> tuple[float, dict[str, float]]:
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        noise_level = float(np.std(gray.astype(np.float32)))
        channel_std = float(np.std([np.std(image_bgr[:, :, c]) for c in range(3)]))

        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        edge_density = float(np.mean(np.hypot(sobel_x, sobel_y)))

        block_size = 8
        h, w = gray.shape
        block_vars: list[float] = []
        for y in range(0, h - block_size, block_size):
            for x in range(0, w - block_size, block_size):
                patch = gray[y : y + block_size, x : x + block_size]
                block_vars.append(float(np.var(patch)))
        block_var_std = float(np.std(block_vars)) if block_vars else 0.0

        score = float(
            np.clip(
                0.25 * _sigmoid((laplacian_var - 120.0) / 40.0)
                + 0.20 * _sigmoid((noise_level - 35.0) / 10.0)
                + 0.20 * _sigmoid((channel_std - 4.0) / 2.0)
                + 0.20 * _sigmoid((edge_density - 25.0) / 8.0)
                + 0.15 * _sigmoid((block_var_std - 180.0) / 60.0),
                0.0,
                1.0,
            )
        )

        return score, {
            "laplacian_variance": round(laplacian_var, 4),
            "noise_level": round(noise_level, 4),
            "channel_std": round(channel_std, 4),
            "edge_density": round(edge_density, 4),
            "block_variance_std": round(block_var_std, 4),
        }


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))
