"""MobileNetV3-Large Indian document type classifier (FP32 ONNX)."""

from __future__ import annotations

import time

import cv2
import numpy as np

from app.core.config import Settings, get_settings
from app.schemas.document_models import DocumentClassificationResult, DocumentTypeCandidate
from app.utils.model_runtime import create_runtime


class DocumentClassifierService:
    """Classify rectified document images into Indian document types."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._runtime = None
        self.labels = self.settings.mobilenet_classifier_labels

    @property
    def runtime(self):
        if self._runtime is None:
            self._runtime = create_runtime(
                self.settings.mobilenet_classifier_onnx_path,
                backend=self.settings.onnx_inference_backend,
                providers=self.settings.onnx_execution_providers or None,
            )
        return self._runtime

    def classify(self, image_bgr: np.ndarray) -> DocumentClassificationResult:
        start = time.perf_counter()
        tensor = self._preprocess(image_bgr)
        logits = self.runtime.infer(tensor=tensor)[0].reshape(-1)
        probs = self._softmax(logits)

        ranked_indices = np.argsort(probs)[::-1]
        top_candidates = [
            DocumentTypeCandidate(
                type=self.labels[int(index)],
                confidence=float(probs[int(index)]),
            )
            for index in ranked_indices[:3]
            if int(index) < len(self.labels)
        ]

        best = top_candidates[0]
        predicted_type = best.type
        confidence = best.confidence
        if confidence < self.settings.mobilenet_classifier_threshold:
            predicted_type = "unknown"
            confidence = float(probs[int(ranked_indices[0])])

        return DocumentClassificationResult(
            document_type=predicted_type,
            confidence=confidence,
            top_candidates=top_candidates,
            model_version=self.settings.mobilenet_model_version,
            runtime_ms=(time.perf_counter() - start) * 1000,
        )

    @staticmethod
    def _preprocess(image_bgr: np.ndarray) -> np.ndarray:
        rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (224, 224), interpolation=cv2.INTER_LINEAR)
        tensor = resized.astype(np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        tensor = (tensor - mean) / std
        return np.transpose(tensor, (2, 0, 1))[None, ...]

    @staticmethod
    def _softmax(logits: np.ndarray) -> np.ndarray:
        shifted = logits - np.max(logits)
        exp = np.exp(shifted)
        return exp / np.sum(exp)
