"""PP-LCNet_x1_0_doc_ori orientation classification."""

from __future__ import annotations

import time
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

from app.core.config import Settings, get_settings
from app.schemas.document_models import OrientationResult


class OrientationService:
    """
    Document orientation classifier (0/90/180/270).

    Loads PP-LCNet assets from `models/pp_lcnet_doc_ori/` when available.
    Falls back to PaddleOCR angle classifier if local PP-LCNet bundle is absent.
    """

    ANGLES = (0, 90, 180, 270)

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def predict(self, image_bgr: np.ndarray) -> OrientationResult:
        start = time.perf_counter()
        angle, confidence = self._predict_angle(image_bgr)
        return OrientationResult(
            angle=angle,
            confidence=confidence,
            model_version=self.settings.pp_lcnet_model_version,
            runtime_ms=(time.perf_counter() - start) * 1000,
        )

    def apply_rotation(self, image_bgr: np.ndarray, angle: int) -> np.ndarray:
        if angle == 0:
            return image_bgr
        if angle == 90:
            return cv2.rotate(image_bgr, cv2.ROTATE_90_CLOCKWISE)
        if angle == 180:
            return cv2.rotate(image_bgr, cv2.ROTATE_180)
        if angle == 270:
            return cv2.rotate(image_bgr, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return image_bgr

    def _predict_angle(self, image_bgr: np.ndarray) -> tuple[int, float]:
        model_dir = self.settings.pp_lcnet_orientation_dir
        onnx_candidates = list(model_dir.glob("*.onnx"))
        if onnx_candidates:
            return self._predict_with_onnx(image_bgr, onnx_candidates[0])

        paddle_dir_files = list(model_dir.glob("*"))
        if paddle_dir_files:
            return self._predict_with_paddle(image_bgr, model_dir)

        return self._predict_with_paddleocr(image_bgr)

    def _predict_with_onnx(self, image_bgr: np.ndarray, model_path: Path) -> tuple[int, float]:
        from app.utils.model_runtime import create_runtime

        runtime = create_runtime(
            model_path,
            backend=self.settings.onnx_inference_backend,
            providers=self.settings.onnx_execution_providers or None,
        )
        resized = cv2.resize(image_bgr, (224, 224), interpolation=cv2.INTER_LINEAR)
        tensor = np.transpose(resized.astype(np.float32) / 255.0, (2, 0, 1))[None, ...]
        logits = runtime.infer(tensor=tensor)[0].reshape(-1)
        probs = self._softmax(logits)
        index = int(np.argmax(probs))
        angle = self.ANGLES[min(index, len(self.ANGLES) - 1)]
        return angle, float(probs[index])

    def _predict_with_paddle(self, image_bgr: np.ndarray, model_dir: Path) -> tuple[int, float]:
        try:
            from paddle.inference import Config, create_predictor
        except ImportError as exc:
            raise RuntimeError(
                "PP-LCNet orientation assets found but Paddle Inference is unavailable."
            ) from exc

        model_file = next(model_dir.glob("*.pdmodel"), None)
        params_file = next(model_dir.glob("*.pdiparams"), None)
        if model_file is None or params_file is None:
            raise FileNotFoundError(
                f"Incomplete PP-LCNet bundle in {model_dir}. Expected pdmodel/pdiparams."
            )

        config = Config(str(model_file), str(params_file))
        config.disable_glog_info()
        predictor = create_predictor(config)
        input_handle = predictor.get_input_handle(predictor.get_input_names()[0])
        resized = cv2.resize(image_bgr, (224, 224)).astype("float32") / 255.0
        tensor = np.transpose(resized, (2, 0, 1))[None, ...]
        input_handle.copy_from_cpu(tensor)
        predictor.run()
        output = predictor.get_output_handle(predictor.get_output_names()[0])
        logits = output.copy_to_cpu().reshape(-1)
        probs = self._softmax(logits)
        index = int(np.argmax(probs))
        return self.ANGLES[min(index, len(self.ANGLES) - 1)], float(probs[index])

    @staticmethod
    @lru_cache(maxsize=1)
    def _get_paddleocr_cls():
        from paddleocr import PaddleOCR

        settings = get_settings()
        return PaddleOCR(
            use_angle_cls=True,
            lang=settings.paddleocr_lang,
            show_log=False,
        )

    def _predict_with_paddleocr(self, image_bgr: np.ndarray) -> tuple[int, float]:
        ocr = self._get_paddleocr_cls()
        result = ocr.ocr(image_bgr, cls=True, det=False, rec=False)
        if not result or not result[0]:
            return 0, 0.5
        angle_info = result[0][0]
        if isinstance(angle_info, (list, tuple)) and len(angle_info) >= 2:
            label = str(angle_info[0]).lower()
            score = float(angle_info[1])
            mapping = {"0": 0, "90": 90, "180": 180, "270": 270}
            for key, value in mapping.items():
                if key in label:
                    return value, score
        return 0, 0.5

    @staticmethod
    def _softmax(logits: np.ndarray) -> np.ndarray:
        shifted = logits - np.max(logits)
        exp = np.exp(shifted)
        return exp / np.sum(exp)
