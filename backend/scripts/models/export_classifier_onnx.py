#!/usr/bin/env python3
"""Export MobileNetV3 classifier checkpoint to FP32 ONNX."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Export classifier to ONNX.")
    parser.add_argument(
        "--weights",
        default="runs/classifier/mobilenetv3_indian_docs.pt",
    )
    parser.add_argument(
        "--output",
        default="models/mobilenetv3_indian_docs.onnx",
    )
    args = parser.parse_args()

    import torch
    import torch.nn as nn
    from torchvision.models import MobileNet_V3_Large_Weights, mobilenet_v3_large

    checkpoint = torch.load(args.weights, map_location="cpu")
    classes = checkpoint.get(
        "classes",
        ["aadhaar", "pan", "passport", "driving_license", "voter_id", "unknown"],
    )

    model = mobilenet_v3_large(weights=None)
    model.classifier[3] = nn.Linear(model.classifier[3].in_features, len(classes))
    model.load_state_dict(checkpoint["model"])
    model.eval()

    dummy = torch.randn(1, 3, 224, 224, dtype=torch.float32)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    torch.onnx.export(
        model,
        dummy,
        output,
        input_names=["input"],
        output_names=["logits"],
        opset_version=17,
        dynamic_axes=None,
    )
    print(f"Exported FP32 ONNX to {output.resolve()}")


if __name__ == "__main__":
    main()
