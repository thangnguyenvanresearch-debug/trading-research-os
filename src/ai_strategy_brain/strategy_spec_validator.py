from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ai_strategy_brain.strategy_spec_schema import (
    ALLOWED_ASSET_CLASSES,
    ALLOWED_ENGINES,
    ALLOWED_INDICATORS,
    ALLOWED_LOGIC_KEYS,
    ALLOWED_OPERATORS,
    REQUIRED_FIELDS,
)
from core.validation import contains_forbidden_logic


def load_strategy_spec(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def validate_strategy_spec(spec: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    missing = REQUIRED_FIELDS - set(spec)
    if missing:
        errors.append(f"Missing required fields: {sorted(missing)}")
    if spec.get("asset_class") not in ALLOWED_ASSET_CLASSES:
        errors.append(f"Unsupported asset_class: {spec.get('asset_class')}")
    if spec.get("engine_target") not in ALLOWED_ENGINES:
        errors.append(f"Unsupported engine_target: {spec.get('engine_target')}")
    if not isinstance(spec.get("pairs"), list) or not spec.get("pairs"):
        errors.append("pairs must be a non-empty list.")
    errors.extend(_validate_logic_block(spec.get("entry_logic"), "entry_logic"))
    errors.extend(_validate_logic_block(spec.get("exit_logic"), "exit_logic"))
    risk = spec.get("risk", {})
    if not isinstance(risk, dict):
        errors.append("risk must be a dict.")
        risk = {}
    if risk.get("leverage_allowed") is not False:
        errors.append("risk.leverage_allowed must be false in v1.")
    if risk.get("futures_allowed") is not False:
        errors.append("risk.futures_allowed must be false in v1.")
    stop_loss = _as_float(risk.get("stop_loss"), "risk.stop_loss", errors)
    take_profit = _as_float(risk.get("take_profit"), "risk.take_profit", errors)
    max_pair_exposure = _as_float(risk.get("max_pair_exposure"), "risk.max_pair_exposure", errors)
    max_open_trades = risk.get("max_open_trades")
    if stop_loss is not None and not (-0.50 < stop_loss < 0):
        errors.append("risk.stop_loss must be negative and greater than -0.50.")
    if take_profit is not None and not (0 < take_profit <= 1):
        errors.append("risk.take_profit must be positive and <= 1.0.")
    if max_pair_exposure is not None and not (0 < max_pair_exposure <= 1):
        errors.append("risk.max_pair_exposure must be > 0 and <= 1.0.")
    if not isinstance(max_open_trades, int) or max_open_trades <= 0:
        errors.append("risk.max_open_trades must be a positive integer.")
    validation = spec.get("validation", {})
    if not isinstance(validation, dict):
        errors.append("validation must be a dict.")
        validation = {}
    if not validation.get("require_fee_model", False):
        errors.append("validation.require_fee_model must be true.")
    if not validation.get("require_slippage_model", False):
        errors.append("validation.require_slippage_model must be true.")
    forbidden = contains_forbidden_logic(yaml.safe_dump(spec).lower())
    if forbidden:
        errors.append(f"Forbidden or suspicious logic: {forbidden}")
    return not errors, errors


def _validate_logic_block(block: Any, label: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(block, dict):
        return [f"{label} must be a dict containing all or any."]
    logic_keys = set(block) & ALLOWED_LOGIC_KEYS
    if len(logic_keys) != 1:
        errors.append(f"{label} must contain exactly one of all/any.")
        return errors
    conditions = block[next(iter(logic_keys))]
    if not isinstance(conditions, list) or not conditions:
        errors.append(f"{label} conditions must be a non-empty list.")
        return errors
    for index, condition in enumerate(conditions):
        if not isinstance(condition, dict):
            errors.append(f"{label}[{index}] condition must be a dict.")
            continue
        indicator = condition.get("indicator")
        operator = condition.get("operator")
        value = condition.get("value")
        if indicator not in ALLOWED_INDICATORS:
            errors.append(f"{label}[{index}] unsupported indicator: {indicator}")
        if operator not in ALLOWED_OPERATORS:
            errors.append(f"{label}[{index}] unsupported operator: {operator}")
        if isinstance(value, str) and value not in ALLOWED_INDICATORS:
            try:
                float(value)
            except ValueError:
                errors.append(f"{label}[{index}] unsupported value reference: {value}")
    return errors


def _as_float(value: Any, label: str, errors: list[str]) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        errors.append(f"{label} must be numeric.")
        return None
