from __future__ import annotations

import pytest

from qlib_brain import qlib_adapter
from qlib_brain.qlib_adapter import assert_qlib_research_only, get_qlib_status


def test_qlib_missing_status_is_safe(monkeypatch) -> None:
    monkeypatch.setattr(qlib_adapter.importlib.util, "find_spec", lambda name: None)

    status = get_qlib_status({"mode": "research_only"})

    assert status["engine"] == "qlib"
    assert status["qlib_import_available"] is False
    assert status["safe_for_live"] is False
    assert status["status"] == "missing"


@pytest.mark.parametrize(
    "key",
    [
        "allow_live_trading",
        "allow_real_orders",
        "allow_brokerage_credentials",
        "allow_cloud_credentials",
        "allow_futures",
        "allow_leverage",
    ],
)
def test_qlib_research_only_rejects_unsafe_flags(key: str) -> None:
    with pytest.raises(ValueError):
        assert_qlib_research_only({"mode": "research_only", key: True})


def test_qlib_research_only_rejects_non_research_mode() -> None:
    with pytest.raises(ValueError):
        assert_qlib_research_only({"mode": "live"})
