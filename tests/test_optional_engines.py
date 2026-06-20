from __future__ import annotations

from data_brain.openbb_adapter import OpenBBAdapter
from core.engine_status import ALLOWED_ENGINE_STATUSES
from data_brain.openbb_adapter import get_openbb_status
from hummingbot_brain.spread_scanner import get_hummingbot_status
from lean_brain.lean_backtest_runner import get_lean_status, lean_cli_status
from nautilus_brain.nautilus_adapter import get_nautilus_status, nautilus_status
from qlib_brain.qlib_experiment_runner import get_qlib_status, run_basic_experiment


def test_missing_optional_engines_return_status_without_crashing() -> None:
    assert "status" in OpenBBAdapter(enabled=False).fetch_context("SPY")
    assert "available" in lean_cli_status()
    assert "status" in run_basic_experiment()
    assert "available" in nautilus_status()


def test_optional_engine_status_shape_is_safe_for_live() -> None:
    statuses = [
        get_openbb_status(),
        get_qlib_status(),
        get_lean_status(),
        get_hummingbot_status(),
        get_nautilus_status(),
    ]
    for status in statuses:
        assert status["status"] in ALLOWED_ENGINE_STATUSES
        assert status["safe_for_live"] is False
        assert status["engine"]
        assert status["current_capability"]
        assert status["next_step"]
