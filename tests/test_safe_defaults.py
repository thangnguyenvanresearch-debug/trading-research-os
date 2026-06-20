from __future__ import annotations

from core.config_loader import load_global_config
from core.models import Permission
from core.validation import assert_research_only


def test_live_permission_does_not_exist() -> None:
    assert "APPROVED_FOR_LIVE" not in {permission.value for permission in Permission}


def test_global_safety_defaults_are_research_only() -> None:
    config = load_global_config()
    safety = config["safety"]
    assert safety["live_trading_enabled"] is False
    assert safety["real_orders_enabled"] is False
    assert safety["leverage_enabled"] is False
    assert safety["futures_enabled"] is False
    assert_research_only(config)

