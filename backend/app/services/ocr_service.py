"""PaddleOCR service for text detection and recognition."""

from __future__ import annotations

import time
from functools import lru_cache

import numpy as np

from app.core.config import Settings, get_settings
from app.schemas.document_models import OCRResult, OCRTextElement


class OCRService:
    """Primary OCR engine using PaddleOCR (det + rec + optional angle cls)."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def recognize(self, image_bgr: np.ndarray) -> OCRResult:
        start = time.perf_counter()
        engine = self._get_engine()
        raw = engine.ocr(image_bgr, cls=self.settings.paddleocr_use_angle_cls)

        elements: list[OCRTextElement] = []
        if raw:
            for line in raw[0] if raw[0] else []:
                if not line or len(line) < 2:
                    continue
                bbox_raw, text_info = line[0], line[1]
                text = str(text_info[0]).strip()
                confidence = float(text_info[1])
                if not text:
                    continue
                bbox = [[float(x), float(y)] for x, y in bbox_raw]
                elements.append(
                    OCRTextElement(text=text, confidence=confidence, bbox=bbox)
                )

        return OCRResult(
            elements=elements,
            engine_version=self.settings.paddleocr_version,
            runtime_ms=(time.perf_counter() - start) * 1000,
        )

    @staticmethod
    @lru_cache(maxsize=1)
    def _get_engine():
        settings = get_settings()
        from paddleocr import PaddleOCR

        use_gpu = False
        try:
            import onnxruntime as ort

            use_gpu = "CUDAExecutionProvider" in ort.get_available_providers()
        except Exception:
            pass

        return PaddleOCR(
            use_angle_cls=settings.paddleocr_use_angle_cls,
            lang=settings.paddleocr_lang,
            use_gpu=use_gpu,
            show_log=False,
        )
