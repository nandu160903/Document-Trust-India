#!/usr/bin/env python3
"""Module 3 API workflow verification using FastAPI TestClient."""

from __future__ import annotations

import argparse
import json
import sys
from io import BytesIO
from pathlib import Path

TESTS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TESTS_ROOT))

from helpers.bootstrap import bootstrap_backend_path, fixture_path

bootstrap_backend_path()

from fastapi.testclient import TestClient
from PIL import Image
import piexif

from app.main import app


def create_sample_image() -> tuple[str, bytes, str]:
    image = Image.new("RGB", (640, 480), color=(235, 235, 235))
    exif_dict = {
        "0th": {piexif.ImageIFD.Software: "Adobe Photoshop CC 2024"},
        "Exif": {},
        "GPS": {},
        "1st": {},
        "thumbnail": None,
    }
    buffer = BytesIO()
    image.save(buffer, format="JPEG", exif=piexif.dump(exif_dict), quality=95)
    return "sample_document.jpg", buffer.getvalue(), "image/jpeg"


def run_api_workflow(file_path: Path | None) -> dict:
    client = TestClient(app)

    health = client.get("/health")
    if health.status_code != 200:
        raise RuntimeError(f"Health check failed: {health.status_code}")

    if file_path:
        filename = file_path.name
        content = file_path.read_bytes()
        content_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".pdf": "application/pdf",
        }.get(file_path.suffix.lower(), "application/octet-stream")
    else:
        filename, content, content_type = create_sample_image()

    response = client.post(
        "/api/v1/upload",
        files={"file": (filename, content, content_type)},
    )

    payload = {
        "health": health.json(),
        "upload_status_code": response.status_code,
        "upload_response": response.json() if response.content else {},
    }

    if response.status_code == 200:
        body = response.json()
        original_url = body.get("original_image_url")
        heatmap_url = body.get("heatmap_image_url")

        if original_url:
            original_resp = client.get(original_url)
            payload["original_asset_status"] = original_resp.status_code

        if heatmap_url:
            heatmap_resp = client.get(heatmap_url)
            payload["heatmap_asset_status"] = heatmap_resp.status_code

    return payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Module 3 upload + analysis API workflow test."
    )
    parser.add_argument(
        "file",
        nargs="?",
        type=Path,
        help="Optional document path. Generates a synthetic JPEG if omitted.",
    )
    args = parser.parse_args()

    if args.file and not args.file.exists():
        fixture_candidate = fixture_path(args.file.name)
        file_path = fixture_candidate if fixture_candidate.exists() else args.file
        if not file_path.exists():
            raise SystemExit(f"File not found: {args.file}")
    else:
        file_path = args.file

    print(json.dumps(run_api_workflow(file_path), indent=2))


if __name__ == "__main__":
    main()
