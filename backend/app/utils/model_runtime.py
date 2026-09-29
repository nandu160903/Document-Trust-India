"""Abstract ONNX inference runtime with GPU/CPU provider selection."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np


class ModelRuntime(ABC):
    """Runtime interface so ONNX Runtime / OpenCV DNN can be swapped."""

    @abstractmethod
    def infer(self, input_name: str, tensor: np.ndarray) -> list[np.ndarray]:
        raise NotImplementedError


class ONNXRuntimeBackend(ModelRuntime):
    """Primary FP32 ONNX Runtime backend."""

    def __init__(self, model_path: Path, providers: list[str] | None = None) -> None:
        import onnxruntime as ort

        if not model_path.exists():
            raise FileNotFoundError(
                f"ONNX model not found: {model_path}. "
                "Train/export the model and place it under backend/models/."
            )

        selected_providers = providers or self._default_providers()
        self.session = ort.InferenceSession(
            str(model_path),
            providers=selected_providers,
        )
        self.input_name = self.session.get_inputs()[0].name
        self.output_names = [item.name for item in self.session.get_outputs()]

    @staticmethod
    def _default_providers() -> list[str]:
        import onnxruntime as ort

        available = ort.get_available_providers()
        if "CUDAExecutionProvider" in available:
            return ["CUDAExecutionProvider", "CPUExecutionProvider"]
        return ["CPUExecutionProvider"]

    def infer(self, input_name: str | None = None, tensor: np.ndarray | None = None) -> list[np.ndarray]:
        if tensor is None:
            raise ValueError("Input tensor is required.")
        name = input_name or self.input_name
        outputs = self.session.run(self.output_names, {name: tensor})
        return outputs


class OpenCVDNNBackend(ModelRuntime):
    """Optional OpenCV DNN backend for the same ONNX graphs."""

    def __init__(self, model_path: Path) -> None:
        import cv2

        if not model_path.exists():
            raise FileNotFoundError(f"ONNX model not found: {model_path}")
        self.net = cv2.dnn.readNetFromONNX(str(model_path))

    def infer(self, input_name: str, tensor: np.ndarray) -> list[np.ndarray]:
        import cv2

        self.net.setInput(tensor)
        output_names = self.net.getUnconnectedOutLayersNames()
        outputs = self.net.forward(output_names)
        if isinstance(outputs, np.ndarray):
            return [outputs]
        return list(outputs)


def create_runtime(
    model_path: Path,
    backend: str = "onnxruntime",
    providers: list[str] | None = None,
) -> ModelRuntime:
    if backend == "opencv_dnn":
        return OpenCVDNNBackend(model_path)
    return ONNXRuntimeBackend(model_path, providers=providers)
