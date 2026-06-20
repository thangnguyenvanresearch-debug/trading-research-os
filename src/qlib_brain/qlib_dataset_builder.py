from __future__ import annotations

from pathlib import Path

from core.paths import DATA_DIR


def qlib_dataset_status() -> dict:
    return {"provider_uri": str(DATA_DIR / "qlib"), "status": "optional_phase_3"}


def ensure_qlib_dirs() -> Path:
    path = DATA_DIR / "qlib"
    path.mkdir(parents=True, exist_ok=True)
    return path

