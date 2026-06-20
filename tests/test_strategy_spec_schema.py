from __future__ import annotations

from ai_strategy_brain.strategy_generator import generate_specs
from ai_strategy_brain.strategy_spec_validator import validate_strategy_spec


def test_generated_crypto_specs_are_valid() -> None:
    specs = generate_specs("crypto", 3, ["BTC/USDT", "ETH/USDT"])
    assert len(specs) == 3
    for spec in specs:
        valid, errors = validate_strategy_spec(spec)
        assert valid, errors
        assert spec["risk"]["leverage_allowed"] is False
        assert spec["risk"]["futures_allowed"] is False


def test_invalid_risk_bounds_and_condition_types_fail() -> None:
    spec = generate_specs("crypto", 1, ["BTC/USDT"])[0]
    spec["risk"]["leverage_allowed"] = True
    spec["risk"]["stop_loss"] = 0.1
    spec["risk"]["take_profit"] = 2
    spec["entry_logic"] = {"all": ["not-a-condition"]}
    valid, errors = validate_strategy_spec(spec)
    assert not valid
    assert any("leverage" in error for error in errors)
    assert any("stop_loss" in error for error in errors)
    assert any("take_profit" in error for error in errors)
    assert any("condition must be a dict" in error for error in errors)
