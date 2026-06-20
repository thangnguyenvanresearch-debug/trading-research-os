from __future__ import annotations

import shutil
from typing import Any

from core.config_loader import load_config
from core.paths import PROJECT_ROOT


FORBIDDEN_LEAN_FLAGS = {
    "allow_live_trading": "live trading",
    "allow_brokerage_credentials": "brokerage credentials",
    "allow_quantconnect_cloud": "QuantConnect cloud",
    "allow_real_orders": "real orders",
    "allow_futures": "futures",
    "allow_leverage": "leverage",
}


def get_lean_status(config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return local LEAN availability without installing, logging in, or using cloud services."""
    active = _lean_config(config)
    lean_cli_path = _lean_cli_path()
    lean_cli = lean_cli_path is not None
    docker = shutil.which("docker") is not None
    warnings: list[str] = []
    errors: list[str] = []
    try:
        assert_lean_research_only(active)
    except ValueError as exc:
        errors.append(str(exc))
    if not lean_cli:
        warnings.append("LEAN CLI is not installed; only data export and research skeleton generation are available.")
    if not docker:
        warnings.append("Docker is not available; local LEAN CLI backtests may not run.")
    return {
        "engine": "lean",
        "mode": "research_only",
        "available": lean_cli,
        "lean_cli_available": lean_cli,
        "lean_cli_path": lean_cli_path,
        "docker_available": docker,
        "safe_for_live": False,
        "status": "ready" if lean_cli and not errors else ("missing" if not lean_cli else "partial"),
        "warnings": warnings,
        "errors": errors,
        "current_capability": (
            "Local LEAN CLI can be attempted for research-only backtests."
            if lean_cli
            else "Research-only data export and LEAN-style project skeleton generation."
        ),
        "next_step": (
            "Run scripts/run_lean_backtest.py for a local backtest."
            if lean_cli
            else "Install LEAN CLI and Docker locally if executable LEAN backtests are needed."
        ),
    }


def assert_lean_research_only(config: dict[str, Any] | None = None) -> None:
    """Reject any LEAN configuration that tries to enable live/cloud/brokerage behavior."""
    active = _lean_config(config)
    enabled = [label for key, label in FORBIDDEN_LEAN_FLAGS.items() if bool(active.get(key, False))]
    if enabled:
        raise ValueError(f"LEAN integration is research-only; forbidden settings enabled: {', '.join(enabled)}")
    mode = str(active.get("mode", "research_only")).lower()
    if mode != "research_only":
        raise ValueError("LEAN integration only supports mode=research_only.")


def _lean_config(config: dict[str, Any] | None = None) -> dict[str, Any]:
    active = {
        "mode": "research_only",
        "allow_live_trading": False,
        "allow_brokerage_credentials": False,
        "allow_quantconnect_cloud": False,
        "allow_real_orders": False,
        "allow_futures": False,
        "allow_leverage": False,
    }
    if config is None:
        try:
            active.update(load_config("lean"))
        except FileNotFoundError:
            pass
    else:
        active.update(config)
    return active


def _lean_cli_path() -> str | None:
    path = shutil.which("lean")
    if path:
        return path
    local = PROJECT_ROOT / ".venv-openbb" / "Scripts" / "lean.exe"
    if local.exists():
        return str(local)
    return None
