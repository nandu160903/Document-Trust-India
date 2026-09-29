#!/usr/bin/env python3
"""Manual verification script for Module 1 forensic services."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.ela_detector import ELADetector
from app.services.metadata_analyzer import MetadataAnalyzer
from app.services.ocr_layout import OCRLayoutAnalyzer


def run_module1_tests(file_path: Path) -> dict:
    metadata = MetadataAnalyzer().analyze(file_path)
    ela = ELADetector().analyze(file_path)
    ocr = OCRLayoutAnalyzer().analyze(file_path)

    return {
        "file": str(file_path.resolve()),
        "metadata": metadata,
        "ela": ela,
        "ocr_layout": ocr,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Module 1 forensic analyzers against a document."
    )
    parser.add_argument(
        "file",
        type=Path,
        help="Path to a JPEG, PNG, or PDF document.",
    )
    args = parser.parse_args()

    if not args.file.exists():
        raise SystemExit(f"File not found: {args.file}")

    results = run_module1_tests(args.file)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
