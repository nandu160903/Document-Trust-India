#!/usr/bin/env python3
"""Module 2 risk engine verification."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TESTS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TESTS_ROOT))

from helpers.bootstrap import bootstrap_backend_path

bootstrap_backend_path()

from app.services.risk_engine import RiskEngine


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Module 1 + Module 2 analysis pipeline."
    )
    parser.add_argument("file", type=Path, help="Path to JPEG, PNG, or PDF.")
    args = parser.parse_args()

    if not args.file.exists():
        raise SystemExit(f"File not found: {args.file}")

    assessment = RiskEngine().analyze_document(args.file)
    print(json.dumps(assessment, indent=2))


if __name__ == "__main__":
    main()
