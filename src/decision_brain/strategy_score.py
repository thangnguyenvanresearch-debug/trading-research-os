from __future__ import annotations


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def score_strategy(metrics: dict, regime_match: bool = True) -> int:
    """Score from 0 to 100 using the configured v1 component weights."""
    oos = clamp((_num(metrics, "out_of_sample_return", 0.0) + 0.05) / 0.20 * 100)
    drawdown = clamp((0.35 - _num(metrics, "max_drawdown", 1.0)) / 0.35 * 100)
    return_quality = clamp(_num(metrics, "profit_factor", 0.0) / 2.0 * 100)
    trade_reliability = clamp(_num(metrics, "trade_count", 0) / 150 * 100)
    regime_fit = 100.0 if regime_match else 40.0
    cost_robustness = clamp((_num(metrics, "fee_slippage_adjusted_return", 0.0) + 0.05) / 0.20 * 100)
    score = (
        oos * 0.25
        + drawdown * 0.20
        + return_quality * 0.15
        + trade_reliability * 0.15
        + regime_fit * 0.15
        + cost_robustness * 0.10
    )
    return int(round(clamp(score)))


def _num(metrics: dict, key: str, default: float) -> float:
    try:
        value = metrics.get(key, default)
        return float(value if value is not None else default)
    except (TypeError, ValueError):
        return default
