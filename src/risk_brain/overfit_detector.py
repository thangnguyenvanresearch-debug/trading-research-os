from __future__ import annotations


def detect_overfit_flags(metrics: dict, rules: dict) -> list[str]:
    flags: list[str] = []
    if _num(metrics, "equity_smoothness", 0) > rules.get("max_equity_curve_smoothness", 0.985):
        flags.append("Suspiciously smooth equity curve.")
    if _num(metrics, "regime_count", 0) <= 1:
        flags.append("Strategy appears to work in only one market regime.")
    if _num(metrics, "pair_concentration", 1) > rules.get("max_pair_concentration", 0.70):
        flags.append("Result depends too heavily on one pair.")
    return flags


def _num(metrics: dict, key: str, default: float) -> float:
    try:
        value = metrics.get(key, default)
        return float(value if value is not None else default)
    except (TypeError, ValueError):
        return default
