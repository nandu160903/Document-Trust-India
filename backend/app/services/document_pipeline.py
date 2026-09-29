"""Milestone-1 document CV pipeline: detect → corners → perspective."""

from __future__ import annotations

import time
import uuid
from pathlib import Path

import cv2

from app.core.config import Settings, get_settings
from app.schemas.document_models import MilestoneOnePipelineResult, PerspectiveResult
from app.services.corner_detector import CornerDetectorService
from app.services.document_detector import DocumentDetectorService
from app.services.perspective import PerspectiveCorrectionService
from app.services.uvdoc_correction import UVDocCorrectionService


class DocumentCVPipeline:
    """
    Upload → OpenCV preprocessing → YOLO26n-seg → mask → corners → perspective.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.detector = DocumentDetectorService(settings=self.settings)
        self.corner_detector = CornerDetectorService()
        self.perspective = PerspectiveCorrectionService(settings=self.settings)
        self.uvdoc = UVDocCorrectionService(settings=self.settings)

    def run(self, image_path: str | Path) -> MilestoneOnePipelineResult:
        request_id = uuid.uuid4().hex
        timings: dict[str, float] = {}
        path = Path(image_path)

        image_bgr = cv2.imread(str(path))
        if image_bgr is None:
            raise ValueError(f"Unable to read image: {path}")

        preprocess_start = time.perf_counter()
        image_bgr = self._preprocess(image_bgr)
        timings["preprocess_ms"] = (time.perf_counter() - preprocess_start) * 1000

        detection, mask = self.detector.detect(image_bgr)
        timings["detector_ms"] = detection.runtime_ms

        if not detection.detected or mask is None:
            return MilestoneOnePipelineResult(
                request_id=request_id,
                document_detection=detection,
                perspective=PerspectiveResult(),
                model_versions=self._model_versions(),
                timings_ms=timings,
            )

        corner_start = time.perf_counter()
        corners, corner_ms = self.corner_detector.extract(mask, image_bgr)
        timings["corner_ms"] = corner_ms + (time.perf_counter() - corner_start) * 1000
        detection.corners = corners

        if corners is None:
            return MilestoneOnePipelineResult(
                request_id=request_id,
                document_detection=detection,
                perspective=PerspectiveResult(),
                model_versions=self._model_versions(),
                timings_ms=timings,
            )

        working = image_bgr
        if self.uvdoc.should_apply(image_bgr, detection.confidence):
            uv_start = time.perf_counter()
            working = self.uvdoc.unwarp(image_bgr)
            timings["uvdoc_ms"] = (time.perf_counter() - uv_start) * 1000

        perspective = self.perspective.rectify(working, corners)
        timings["perspective_ms"] = perspective.runtime_ms
        timings["total_ms"] = sum(timings.values())

        return MilestoneOnePipelineResult(
            request_id=request_id,
            document_detection=detection,
            perspective=perspective,
            model_versions=self._model_versions(),
            timings_ms=timings,
        )

    @staticmethod
    def _preprocess(image_bgr: np.ndarray) -> np.ndarray:
        return cv2.convertScaleAbs(image_bgr, alpha=1.05, beta=5)

    def _model_versions(self) -> dict[str, str]:
        return {
            "detector": self.settings.yolo_model_version,
            "classifier": self.settings.mobilenet_model_version,
            "orientation": self.settings.pp_lcnet_model_version,
            "ocr": self.settings.paddleocr_version,
            "uvdoc": self.settings.uvdoc_model_version,
        }
