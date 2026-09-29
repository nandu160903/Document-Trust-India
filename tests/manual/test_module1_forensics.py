#!/usr/bin/env python3
"""Module 1 forensic service verification."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TESTS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TESTS_ROOT))

from helpers.bootstrap import bootstrap_backend_path

bootstrap_backend_path()

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
    parser.add_argument("file", type=Path, help="Path to JPEG, PNG, or PDF.")
    args = parser.parse_args()

    if not args.file.exists():
        raise SystemExit(f"File not found: {args.file}")

    print(json.dumps(run_module1_tests(args.file), indent=2))


if __name__ == "__main__":
    main()
