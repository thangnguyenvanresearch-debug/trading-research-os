from __future__ import annotations

import importlib
import importlib.metadata
import importlib.util
from typing import Any

from core.config_loader import load_config


FORBIDDEN_QLIB_FLAGS = {
    "allow_live_trading": "live trading",
    "allow_real_orders": "real orders",
    "allow_brokerage_credentials": "brokerage credentials",
    "allow_cloud_credentials": "cloud credentials",
    "allow_futures": "futures",
    "allow_leverage": "leverage",
}


def get_qlib_status(config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return optional Qlib availability without installing or fetching remote datasets."""
    active = _qlib_config(config)
    warnings: list[str] = []
    errors: list[str] = []
    try:
        assert_qlib_research_only(active)
    except ValueError as exc:
        errors.append(str(exc))
    available = importlib.util.find_spec("qlib") is not None
    version = None
    if available:
        try:
            version = importlib.metadata.version("pyqlib")
        except importlib.metadata.PackageNotFoundError:
            try:
                version = importlib.metadata.version("qlib")
            except importlib.metadata.PackageNotFoundError:
                version = "unknown"
    else:
        warnings.append("Qlib is not installed; dataset export works, but Qlib execution is unavailable.")
    return {
        "engine": "qlib",
        "mode": "research_only",
        "available": available and not errors,
        "qlib_import_available": available,
        "version": version,
        "safe_for_live": False,
        "status": "partial" if available and not errors else ("missing" if not available else "blocked"),
        "warnings": warnings,
        "errors": errors,
        "current_capability": (
            "Qlib package detected; local research experiments can be attempted against exported local data."
            if available
            else "Local OpenBB-to-Qlib-style dataset export and unavailable-run reporting."
        ),
        "next_step": (
            "Run scripts/run_qlib_experiment.py for a local research experiment."
            if available
            else "Install Qlib locally if true Qlib ML/factor experiments are needed."
        ),
    }


def assert_qlib_research_only(config: dict[str, Any] | None = None) -> None:
    """Reject any Qlib configuration that tries to enable execution/live behavior."""
    active = _qlib_config(config)
    enabled = [label for key, label in FORBIDDEN_QLIB_FLAGS.items() if bool(active.get(key, False))]
    if enabled:
        raise ValueError(f"Qlib integration is research-only; forbidden settings enabled: {', '.join(enabled)}")
    if str(active.get("mode", "research_only")).lower() != "research_only":
        raise ValueError("Qlib integration only supports mode=research_only.")


def import_qlib_module() -> Any | None:
    """Import Qlib only when available. No installation or remote data fetch is attempted."""
    if importlib.util.find_spec("qlib") is None:
        return None
    return importlib.import_module("qlib")


def _qlib_config(config: dict[str, Any] | None = None) -> dict[str, Any]:
    active: dict[str, Any] = {
        "mode": "research_only",
        "allow_live_trading": False,
        "allow_real_orders": False,
        "allow_brokerage_credentials": False,
        "allow_cloud_credentials": False,
        "allow_futures": False,
        "allow_leverage": False,
    }
    if config is None:
        try:
            active.update(load_config("qlib"))
        except FileNotFoundError:
            pass
    else:
        active.update(config)
    return active
