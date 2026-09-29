#!/usr/bin/env python3
"""End-to-end workflow runner for all manual verification scripts."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MANUAL_DIR = Path(__file__).resolve().parent


def run_script(script_name: str, file_arg: Path | None) -> int:
    script_path = MANUAL_DIR / script_name
    command = [sys.executable, str(script_path)]
    if file_arg is not None:
        command.append(str(file_arg))
    completed = subprocess.run(command, cwd=REPO_ROOT, check=False)
    return completed.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="Run all DocumentTrust manual tests.")
    parser.add_argument(
        "file",
        nargs="?",
        type=Path,
        help="Optional shared document for Module 1 and 2 tests.",
    )
    args = parser.parse_args()

    steps = [
        ("Module 1 forensic services", "test_module1_forensics.py", args.file),
        ("Module 2 risk engine", "test_module2_risk_engine.py", args.file),
        ("Module 3 API workflow", "test_module3_api_workflow.py", args.file),
    ]

    for label, script, file_arg in steps:
        print(f"\n=== {label} ===")
        exit_code = run_script(script, file_arg if script != "test_module3_api_workflow.py" else args.file)
        if exit_code != 0:
            raise SystemExit(exit_code)

    print("\nAll manual workflow tests completed successfully.")


if __name__ == "__main__":
    main()
