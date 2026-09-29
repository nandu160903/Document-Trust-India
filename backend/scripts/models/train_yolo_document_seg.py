#!/usr/bin/env python3
"""Train YOLO26n-seg (or compatible) one-class document segmentation model."""

from __future__ import annotations

import argparse
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]


def resolve_device(requested: str) -> str:
    """Use GPU when available; otherwise fall back to CPU."""
    import torch

    if requested == "auto":
        return "0" if torch.cuda.is_available() else "cpu"
    if requested.isdigit() and not torch.cuda.is_available():
        print("CUDA is not available on this machine; using CPU instead.")
        return "cpu"
    return requested


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
    parser.add_argument(
        "--device",
        default="auto",
        help="Training device: auto (default), cpu, 0, 0,1, etc.",
    )
    args = parser.parse_args()
    device = resolve_device(args.device)

    data_path = Path(args.data)
    if not data_path.is_absolute():
        data_path = (BACKEND_DIR / data_path).resolve()
    if not data_path.exists():
        raise SystemExit(
            f"Dataset YAML not found: {data_path}\n"
            "Create it under backend/datasets/document/ and add train/val images + labels."
        )

    train_images = BACKEND_DIR / "datasets" / "document" / "images" / "train"
    image_files = [
        *train_images.glob("*.jpg"),
        *train_images.glob("*.jpeg"),
        *train_images.glob("*.png"),
        *train_images.glob("*.webp"),
    ]
    if not image_files:
        raise SystemExit(
            "No training images found in backend/datasets/document/images/train.\n"
            "Add labeled photos, or generate a smoke-test set:\n"
            "  python3 scripts/models/generate_synthetic_document_dataset.py"
        )

    from ultralytics import YOLO

    model = YOLO(args.model)
    model.train(
        data=str(data_path),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=device,
        project=str(BACKEND_DIR / "runs" / "segment"),
        name="document_yolo26n_seg",
    )


if __name__ == "__main__":
    main()
