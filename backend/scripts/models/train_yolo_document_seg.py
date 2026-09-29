#!/usr/bin/env python3
"""Train YOLO26n-seg (or compatible) one-class document segmentation model."""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Train document segmentation model.")
    parser.add_argument("--data", required=True, help="Path to dataset YAML.")
    parser.add_argument(
        "--model",
        default="yolo11n-seg.pt",
        help="Base segmentation model. Replace with yolo26n-seg.pt when available.",
    )
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--device", default="0")
    args = parser.parse_args()

    from ultralytics import YOLO

    model = YOLO(args.model)
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project="runs/segment",
        name="document_yolo26n_seg",
        classes=["document"],
    )


if __name__ == "__main__":
    main()
