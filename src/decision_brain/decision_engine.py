from __future__ import annotations

import json

import yaml

from core.database import fetch_dataframe, insert_dict, utc_now
from core.models import Permission
from decision_brain.explanation_engine import build_reasons
from decision_brain.signal_aggregator import signal_from_status
from decision_brain.strategy_score import score_strategy
from risk_brain.risk_gate import run_risk_reviews


STATUS_PERMISSION = {
    "rejected": Permission.REJECTED,
    "watchlist": Permission.WATCHLIST,
    "paper_only": Permission.PAPER_ONLY,
    "approved_for_dry_run": Permission.APPROVED_FOR_DRY_RUN,
    "archived": Permission.REJECTED,
}


def build_decisions() -> list[dict]:
    if fetch_dataframe("SELECT * FROM risk_reviews").empty:
        run_risk_reviews()
    metrics = fetch_dataframe(
        """
        SELECT bm.*, rr.status, rr.flags, ss.strategy_name, ss.source_yaml
        FROM backtest_metrics bm
        LEFT JOIN risk_reviews rr ON rr.run_id = bm.run_id
        LEFT JOIN strategy_specs ss ON ss.strategy_id = bm.strategy_id
        """
    )
    regimes = fetch_dataframe("SELECT * FROM regimes ORDER BY timestamp DESC")
    latest_regime = regimes.iloc[0]["regime"] if not regimes.empty else "unknown"
    decisions: list[dict] = []
    for _, row in metrics.iterrows():
        row_dict = row.to_dict()
        spec = yaml.safe_load(row.get("source_yaml") or "{}") or {}
        symbols = _decision_symbols(row_dict, spec)
        regime_match = _regime_matches(latest_regime, spec.get("regime_fit", []))
        score = score_strategy(row_dict, regime_match=regime_match)
        permission = STATUS_PERMISSION.get(row.get("status", "rejected"), Permission.REJECTED)
        signal = signal_from_status(str(row.get("status", "rejected")), score)
        risk_flags = json.loads(row.get("flags") or "[]")
        for symbol in symbols:
            decision = {
                "decision_id": _decision_id(row["run_id"], row["strategy_id"], symbol),
                "symbol": symbol,
                "strategy_id": row["strategy_id"],
                "strategy_name": row["strategy_name"] or row["strategy_id"],
                "run_id": row["run_id"],
                "signal": signal.value,
                "permission": permission.value,
                "score": score,
                "regime": latest_regime,
                "reasons": json.dumps(
                    build_reasons(row["strategy_id"], latest_regime, score)
                    + [f"Decision generated for {symbol}.", f"Source backtest run: {row['run_id']}."]
                ),
                "risk_flags": json.dumps(risk_flags),
                "created_at": utc_now(),
            }
            insert_dict("decisions", decision)
            decisions.append(decision)
    return decisions


def _decision_symbols(metrics: dict, spec: dict) -> list[str]:
    pair_metrics_raw = metrics.get("pair_level_metrics")
    if isinstance(pair_metrics_raw, str) and pair_metrics_raw:
        try:
            pair_metrics = json.loads(pair_metrics_raw)
            if pair_metrics:
                return sorted(pair_metrics)
        except json.JSONDecodeError:
            pass
    if metrics.get("symbol"):
        return [str(metrics["symbol"])]
    pairs = spec.get("pairs")
    if isinstance(pairs, list) and pairs:
        return [str(pair) for pair in pairs]
    return ["UNKNOWN"]


def _regime_matches(current_regime: str, regime_fit: list[str]) -> bool:
    if not current_regime or current_regime == "unknown" or not regime_fit:
        return False
    return any(str(regime).lower() in current_regime.lower() for regime in regime_fit)


def _decision_id(run_id: str, strategy_id: str, symbol: str) -> str:
    normalized = symbol.replace("/", "_").replace(":", "_").replace(" ", "_")
    return f"dec_{run_id}_{strategy_id}_{normalized}"
