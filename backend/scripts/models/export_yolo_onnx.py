#!/usr/bin/env python3
"""Export trained YOLO segmentation weights to FP32 ONNX."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Export YOLO seg model to ONNX.")
    parser.add_argument(
        "--weights",
        default="runs/segment/document_yolo26n_seg/weights/best.pt",
        help="Trained .pt weights path.",
    )
    parser.add_argument(
        "--output",
        default="models/yolo26n_seg_document.onnx",
        help="Output ONNX path.",
    )
    parser.add_argument("--imgsz", type=int, default=640)
    args = parser.parse_args()

    from ultralytics import YOLO

    model = YOLO(args.weights)
    export_path = model.export(
        format="onnx",
        imgsz=args.imgsz,
        opset=17,
        simplify=True,
        dynamic=False,
        half=False,
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    Path(export_path).replace(output)
    print(f"Exported FP32 ONNX to {output.resolve()}")


if __name__ == "__main__":
    main()
