from __future__ import annotations

from qlib_brain.qlib_adapter import get_qlib_status


def qlib_available() -> bool:
    return bool(get_qlib_status()["qlib_import_available"])


def run_basic_experiment() -> dict:
    status = get_qlib_status()
    if not status["qlib_import_available"]:
        return {"status": "qlib_not_installed", "message": "Install Qlib for local ML experiments."}
    return {"status": "qlib_available", "message": "Use scripts/run_qlib_experiment.py for research-only runs."}
