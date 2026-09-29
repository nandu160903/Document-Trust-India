#!/usr/bin/env python3
"""Manual verification script for Module 2 risk engine."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.risk_engine import RiskEngine


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run full Module 1 + Module 2 analysis pipeline."
    )
    parser.add_argument(
        "file",
        type=Path,
        help="Path to a JPEG, PNG, or PDF document.",
    )
    args = parser.parse_args()

    if not args.file.exists():
        raise SystemExit(f"File not found: {args.file}")

    assessment = RiskEngine().analyze_document(args.file)
    print(json.dumps(assessment, indent=2))


if __name__ == "__main__":
    main()
