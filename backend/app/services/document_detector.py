"""YOLO26n-seg document localization via FP32 ONNX."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from app.core.config import Settings, get_settings
from app.schemas.document_models import DocumentDetectionResult
from app.utils.image_utils import letterbox, to_chw_float
from app.utils.model_runtime import create_runtime


@dataclass
class _DetectionCandidate:
    confidence: float
    bbox: np.ndarray
    mask: np.ndarray


class DocumentDetectorService:
    """
    Primary document localization using fine-tuned YOLO26n-seg exported to ONNX.

    Expects a single custom class: `document`.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._runtime = None

    @property
    def runtime(self):
        if self._runtime is None:
            providers = self.settings.onnx_execution_providers or None
            self._runtime = create_runtime(
                self.settings.yolo_seg_onnx_path,
                backend=self.settings.onnx_inference_backend,
                providers=providers,
            )
        return self._runtime

    def detect(
        self,
        image_bgr: np.ndarray,
        *,
        save_mask_path: Path | None = None,
    ) -> tuple[DocumentDetectionResult, np.ndarray | None]:
        start = time.perf_counter()
        candidates = self._run_segmentation(image_bgr)
        if not candidates:
            return (
                DocumentDetectionResult(
                    detected=False,
                    confidence=0.0,
                    model_version=self.settings.yolo_model_version,
                    runtime_ms=(time.perf_counter() - start) * 1000,
                ),
                None,
            )

        best = max(candidates, key=lambda item: item.confidence)
        mask = best.mask

        mask_path = save_mask_path
        if mask_path is None:
            mask_path = (
                self.settings.detection_mask_dir / f"{uuid.uuid4().hex}_mask.png"
            )
        cv2.imwrite(str(mask_path), (mask * 255).astype(np.uint8))

        x1, y1, x2, y2 = best.bbox.tolist()
        elapsed = (time.perf_counter() - start) * 1000
        return (
            DocumentDetectionResult(
                detected=True,
                confidence=float(best.confidence),
                bbox=[float(x1), float(y1), float(x2), float(y2)],
                mask_path=str(mask_path.resolve()),
                model_version=self.settings.yolo_model_version,
                runtime_ms=elapsed,
            ),
            mask,
        )

    def _run_segmentation(self, image_bgr: np.ndarray) -> list[_DetectionCandidate]:
        input_size = self.settings.yolo_input_size
        padded, ratio, pad = letterbox(image_bgr, (input_size, input_size))
        tensor = to_chw_float(padded)
        outputs = self.runtime.infer(tensor=tensor)

        if len(outputs) == 1:
            return self._parse_single_output(outputs[0], image_bgr.shape, ratio, pad)
        return self._parse_seg_outputs(outputs, image_bgr.shape, ratio, pad)

    def _parse_seg_outputs(
        self,
        outputs: list[np.ndarray],
        image_shape: tuple[int, int, int],
        ratio: float,
        pad: tuple[float, float],
    ) -> list[_DetectionCandidate]:
        predictions = outputs[0][0]
        protos = outputs[1][0]
        num_classes = 1
        mask_dim = protos.shape[0]
        box_offset = 4 + num_classes

        candidates: list[_DetectionCandidate] = []
        for row in predictions.T:
            class_scores = row[4 : 4 + num_classes]
            confidence = float(np.max(class_scores))
            if confidence < self.settings.yolo_confidence_threshold:
                continue

            cx, cy, w, h = row[:4]
            x1 = (cx - w / 2 - pad[0]) / ratio
            y1 = (cy - h / 2 - pad[1]) / ratio
            x2 = (cx + w / 2 - pad[0]) / ratio
            y2 = (cy + h / 2 - pad[1]) / ratio

            mask_coeff = row[box_offset : box_offset + mask_dim]
            mask = self._decode_mask(mask_coeff, protos, (x1, y1, x2, y2), image_shape)
            candidates.append(
                _DetectionCandidate(
                    confidence=confidence,
                    bbox=np.array([x1, y1, x2, y2], dtype=np.float32),
                    mask=mask,
                )
            )

        return self._nms_candidates(candidates)

    def _parse_single_output(
        self,
        output: np.ndarray,
        image_shape: tuple[int, int, int],
        ratio: float,
        pad: tuple[float, float],
    ) -> list[_DetectionCandidate]:
        # Fallback parser for detector-only ONNX exports.
        rows = output[0] if output.ndim == 3 else output
        candidates: list[_DetectionCandidate] = []
        for row in rows.T if rows.shape[0] < rows.shape[1] else rows:
            if row.shape[0] < 5:
                continue
            confidence = float(row[4])
            if confidence < self.settings.yolo_confidence_threshold:
                continue
            cx, cy, w, h = row[:4]
            x1 = (cx - w / 2 - pad[0]) / ratio
            y1 = (cy - h / 2 - pad[1]) / ratio
            x2 = (cx + w / 2 - pad[0]) / ratio
            y2 = (cy + h / 2 - pad[1]) / ratio
            mask = np.zeros(image_shape[:2], dtype=np.uint8)
            cv2.rectangle(
                mask,
                (int(max(x1, 0)), int(max(y1, 0))),
                (int(min(x2, image_shape[1] - 1)), int(min(y2, image_shape[0] - 1))),
                1,
                -1,
            )
            candidates.append(
                _DetectionCandidate(
                    confidence=confidence,
                    bbox=np.array([x1, y1, x2, y2], dtype=np.float32),
                    mask=mask,
                )
            )
        return self._nms_candidates(candidates)

    def _decode_mask(
        self,
        coeff: np.ndarray,
        protos: np.ndarray,
        bbox: tuple[float, float, float, float],
        image_shape: tuple[int, int, int],
    ) -> np.ndarray:
        mask = coeff @ protos.reshape(protos.shape[0], -1)
        mask = mask.reshape(protos.shape[1], protos.shape[2])
        mask = 1 / (1 + np.exp(-mask))

        x1, y1, x2, y2 = bbox
        height, width = image_shape[:2]
        mx1 = int(max(min(x1, x2), 0))
        my1 = int(max(min(y1, y2), 0))
        mx2 = int(min(max(x1, x2), width - 1))
        my2 = int(min(max(y1, y2), height - 1))

        mask_resized = cv2.resize(mask, (width, height), interpolation=cv2.INTER_LINEAR)
        binary = (mask_resized > 0.5).astype(np.uint8)
        if mx2 > mx1 and my2 > my1:
            cropped = np.zeros_like(binary)
            cropped[my1:my2, mx1:mx2] = binary[my1:my2, mx1:mx2]
            return cropped
        return binary

    def _nms_candidates(
        self,
        candidates: list[_DetectionCandidate],
    ) -> list[_DetectionCandidate]:
        if not candidates:
            return []
        boxes = np.array([item.bbox for item in candidates], dtype=np.float32)
        scores = np.array([item.confidence for item in candidates], dtype=np.float32)
        indices = cv2.dnn.NMSBoxes(
            boxes.tolist(),
            scores.tolist(),
            self.settings.yolo_confidence_threshold,
            self.settings.yolo_iou_threshold,
        )
        if len(indices) == 0:
            return []
        selected = [candidates[int(i)] for i in np.array(indices).reshape(-1)]
        return selected
