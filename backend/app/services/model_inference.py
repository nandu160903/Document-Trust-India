"""Deep learning and heuristic model inference for document tampering."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import cv2
import numpy as np

from app.core.config import Settings, get_settings
from app.schemas.forensics import ModelInferenceResult
from app.services.forensics_utils import load_document_rgb, pil_to_numpy

logger = logging.getLogger(__name__)

InferenceMethod = Literal["transformers_vit", "heuristic_cv"]


@dataclass
class _ViTRuntime:
    model: object
    processor: object
    device: str


class ModelInferenceService:
    """
    Modular forgery inference wrapper.

    Attempts Hugging Face ViT feature extraction first; falls back to
    computer-vision heuristics when model weights are unavailable offline.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._vit_runtime: _ViTRuntime | None = None
        self._vit_load_failed = False

    def predict(self, file_path: str | Path) -> ModelInferenceResult:
        path = Path(file_path)
        image = load_document_rgb(path)
        image_bgr = pil_to_numpy(image)

        if self.settings.enable_transformers_inference and not self._vit_load_failed:
            try:
                score, details = self._predict_with_vit(image)
                return {
                    "anomaly_score": round(score, 4),
                    "method": "transformers_vit",
                    "model_id": self.settings.hf_model_id,
                    "details": details,
                }
            except Exception as exc:
                self._vit_load_failed = True
                logger.warning("ViT inference unavailable, using heuristic fallback: %s", exc)

        score, details = self._predict_with_heuristics(image_bgr)
        return {
            "anomaly_score": round(score, 4),
            "method": "heuristic_cv",
            "model_id": "opencv-heuristic-v1",
            "details": details,
        }

    def _predict_with_vit(self, image) -> tuple[float, dict[str, float]]:
        runtime = self._get_vit_runtime()
        import torch

        inputs = runtime.processor(images=image, return_tensors="pt")
        inputs = {key: value.to(runtime.device) for key, value in inputs.items()}

        with torch.no_grad():
            outputs = runtime.model(**inputs)

        if hasattr(outputs, "logits"):
            logits = outputs.logits.squeeze(0)
            if logits.ndim == 0:
                probability = torch.sigmoid(logits).item()
            else:
                probabilities = torch.softmax(logits, dim=-1)
                probability = probabilities.max().item()
            return float(probability), {"logit_max": float(logits.max().item())}

        hidden = outputs.last_hidden_state if hasattr(outputs, "last_hidden_state") else outputs[0]
        cls_embedding = hidden[:, 0, :].squeeze(0).detach().cpu().numpy()
        score, details = self._score_embedding(cls_embedding)
        return score, details

    def _get_vit_runtime(self) -> _ViTRuntime:
        if self._vit_runtime is not None:
            return self._vit_runtime

        import torch
        from transformers import AutoImageProcessor, AutoModelForImageClassification

        device = "cuda" if torch.cuda.is_available() else "cpu"
        model_id = self.settings.hf_model_id

        try:
            processor = AutoImageProcessor.from_pretrained(model_id)
            model = AutoModelForImageClassification.from_pretrained(model_id)
        except Exception:
            from transformers import AutoModel

            processor = AutoImageProcessor.from_pretrained(model_id)
            model = AutoModel.from_pretrained(model_id)

        model.eval()
        model.to(device)
        self._vit_runtime = _ViTRuntime(model=model, processor=processor, device=device)
        return self._vit_runtime

    def _score_embedding(self, embedding: np.ndarray) -> tuple[float, dict[str, float]]:
        norm = float(np.linalg.norm(embedding))
        std = float(np.std(embedding))
        sparsity = float(np.mean(np.abs(embedding) < 0.05))
        kurtosis_proxy = float(np.mean((embedding - np.mean(embedding)) ** 4))

        # Map embedding statistics to an anomaly proxy in [0, 1].
        raw = (
            0.35 * _sigmoid((norm - 95.0) / 8.0)
            + 0.30 * _sigmoid((std - 0.45) / 0.08)
            + 0.20 * sparsity
            + 0.15 * _sigmoid((kurtosis_proxy - 2.5) / 1.5)
        )
        return float(np.clip(raw, 0.0, 1.0)), {
            "embedding_norm": round(norm, 4),
            "embedding_std": round(std, 4),
            "embedding_sparsity": round(sparsity, 4),
            "embedding_kurtosis_proxy": round(kurtosis_proxy, 4),
        }

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
        block_vars = []
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
