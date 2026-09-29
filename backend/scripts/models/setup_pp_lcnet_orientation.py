#!/usr/bin/env python3
"""Download PP-LCNet document orientation model files into backend/models/."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch PP-LCNet_x1_0_doc_ori assets for local orientation inference."
    )
    parser.add_argument(
        "--output-dir",
        default="models/pp_lcnet_doc_ori",
        help="Directory to store orientation model files.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        from paddleocr import PaddleOCR
    except ImportError as exc:
        raise SystemExit(
            "paddleocr is required. Install backend/requirements.txt first."
        ) from exc

    # Initializing PaddleOCR triggers download of bundled orientation/classification assets.
    PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
    print(
        "PaddleOCR initialized. Copy orientation model files from the PaddleOCR "
        f"cache into {output_dir.resolve()} if you need an explicit local bundle."
    )


if __name__ == "__main__":
    main()
