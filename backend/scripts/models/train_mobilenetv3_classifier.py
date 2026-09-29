#!/usr/bin/env python3
"""Fine-tune MobileNetV3-Large for Indian document classification."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Train MobileNetV3 document classifier.")
    parser.add_argument("--data-dir", required=True, help="ImageFolder dataset root.")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument(
        "--output",
        default="runs/classifier/mobilenetv3_indian_docs.pt",
    )
    args = parser.parse_args()

    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader
    from torchvision import datasets, transforms
    from torchvision.models import MobileNet_V3_Large_Weights, mobilenet_v3_large

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    classes = ["aadhaar", "pan", "passport", "driving_license", "voter_id", "unknown"]

    transform = transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.RandomApply(
                [transforms.ColorJitter(0.2, 0.2, 0.2, 0.05)], p=0.7
            ),
            transforms.RandomRotation(10),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ]
    )

    dataset = datasets.ImageFolder(args.data_dir, transform=transform)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, num_workers=2)

    model = mobilenet_v3_large(weights=MobileNet_V3_Large_Weights.IMAGENET1K_V2)
    model.classifier[3] = nn.Linear(model.classifier[3].in_features, len(classes))
    model.to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)
    criterion = nn.CrossEntropyLoss()

    model.train()
    for _ in range(args.epochs):
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)
            optimizer.zero_grad()
            logits = model(images)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"model": model.state_dict(), "classes": classes}, output)
    print(f"Saved classifier weights to {output.resolve()}")


if __name__ == "__main__":
    main()
