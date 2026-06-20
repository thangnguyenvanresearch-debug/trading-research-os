from __future__ import annotations

import json
from pathlib import Path
from typing import Any


STANDARD_FIELDS = {
    "engine": "freqtrade_cli",
    "total_return": None,
    "max_drawdown": None,
    "win_rate": None,
    "trade_count": None,
    "profit_factor": None,
    "sharpe": None,
    "sortino": None,
    "avg_profit": None,
    "avg_win": None,
    "avg_loss": None,
    "best_pair": None,
    "worst_pair": None,
    "pair_level_metrics": {},
    "fee_adjusted_return": None,
    "slippage_adjusted_return": None,
    "fee_slippage_adjusted_return": None,
    "parser_warnings": [],
}


FIELD_ALIASES = {
    "total_return": ["profit_total", "profit_total_abs", "total_profit", "total_return"],
    "max_drawdown": ["max_drawdown", "max_drawdown_abs", "drawdown"],
    "win_rate": ["winrate", "win_rate", "winning_percent"],
    "trade_count": ["total_trades", "trade_count", "trades"],
    "profit_factor": ["profit_factor"],
    "sharpe": ["sharpe", "sharpe_ratio"],
    "sortino": ["sortino", "sortino_ratio"],
    "avg_profit": ["profit_mean", "avg_profit", "average_profit"],
    "avg_win": ["avg_win", "winning_profit_mean", "profit_mean_win"],
    "avg_loss": ["avg_loss", "losing_profit_mean", "profit_mean_loss"],
    "fee_adjusted_return": ["fee_adjusted_return"],
    "slippage_adjusted_return": ["slippage_adjusted_return"],
    "fee_slippage_adjusted_return": ["fee_slippage_adjusted_return", "profit_total_after_costs"],
}


def parse_freqtrade_result(path: str | Path, strategy_name: str | None = None) -> dict[str, Any]:
    """Parse a Freqtrade backtest export into the Trading Research OS metric shape."""
    result = dict(STANDARD_FIELDS)
    result["pair_level_metrics"] = {}
    result["parser_warnings"] = []
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    payload = _select_strategy_payload(data, strategy_name)
    if payload is None:
        result["parser_warnings"].append("No strategy payload found in Freqtrade export.")
        return result

    for target, aliases in FIELD_ALIASES.items():
        value = _first_present(payload, aliases)
        if value is None:
            result["parser_warnings"].append(f"Missing field: {target}")
            continue
        result[target] = _as_int(value) if target == "trade_count" else _as_float(value)

    pairs = _extract_pair_metrics(payload)
    result["pair_level_metrics"] = pairs
    if pairs:
        sorted_pairs = sorted(
            pairs.items(),
            key=lambda item: _as_float(item[1].get("total_return")) or 0.0,
            reverse=True,
        )
        result["best_pair"] = sorted_pairs[0][0]
        result["worst_pair"] = sorted_pairs[-1][0]
    else:
        result["parser_warnings"].append("Missing pair-level metrics.")

    if result["fee_slippage_adjusted_return"] is None:
        result["fee_slippage_adjusted_return"] = result["fee_adjusted_return"] or result["total_return"]
        if result["fee_adjusted_return"] is None:
            result["parser_warnings"].append(
                "Using total_return as fee_slippage_adjusted_return because adjusted returns were absent."
            )
    return result


def _select_strategy_payload(data: Any, strategy_name: str | None) -> dict[str, Any] | None:
    if not isinstance(data, dict):
        return None
    strategy_block = data.get("strategy")
    if isinstance(strategy_block, dict) and strategy_block:
        if strategy_name and strategy_name in strategy_block and isinstance(strategy_block[strategy_name], dict):
            return strategy_block[strategy_name]
        first = next(iter(strategy_block.values()))
        return first if isinstance(first, dict) else None
    if any(alias in data for aliases in FIELD_ALIASES.values() for alias in aliases):
        return data
    return None


def _first_present(payload: dict[str, Any], aliases: list[str]) -> Any:
    for alias in aliases:
        if alias in payload:
            return payload[alias]
    return None


def _extract_pair_metrics(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw_pairs = (
        payload.get("results_per_pair")
        or payload.get("results_per_pair_with_tags")
        or payload.get("pair_results")
        or payload.get("pairs")
    )
    if not raw_pairs:
        return {}
    pair_metrics: dict[str, dict[str, Any]] = {}
    if isinstance(raw_pairs, dict):
        iterator = raw_pairs.items()
    elif isinstance(raw_pairs, list):
        iterator = ((_pair_name(item), item) for item in raw_pairs if isinstance(item, dict))
    else:
        return {}
    for pair, row in iterator:
        if not pair or not isinstance(row, dict):
            continue
        pair_metrics[str(pair)] = {
            "total_return": _as_float(
                row.get("profit_total")
                or row.get("profit_total_abs")
                or row.get("total_profit")
                or row.get("total_return")
            ),
            "trade_count": _as_int(row.get("total_trades") or row.get("trade_count") or row.get("trades")),
            "win_rate": _as_float(row.get("winrate") or row.get("win_rate")),
            "profit_factor": _as_float(row.get("profit_factor")),
        }
    return pair_metrics


def _pair_name(row: dict[str, Any]) -> str | None:
    value = row.get("key") or row.get("pair") or row.get("symbol")
    if isinstance(value, list) and value:
        return str(value[0])
    return str(value) if value else None


def _as_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None
