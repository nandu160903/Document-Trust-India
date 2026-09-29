"""Shared bootstrap helpers for manual/integration tests."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"


def bootstrap_backend_path() -> Path:
    """Ensure backend package imports resolve when running from tests/."""
    backend_str = str(BACKEND_ROOT)
    if backend_str not in sys.path:
        sys.path.insert(0, backend_str)
    return BACKEND_ROOT


def fixture_path(name: str) -> Path:
    return FIXTURES_DIR / name
