from __future__ import annotations

import json
from pathlib import Path

from core.config_loader import load_config
from core.database import execute, fetch_dataframe, insert_dict, utc_now
from core.models import StrategyStatus
from core.validation import analyze_python_lookahead_risk, contains_forbidden_logic
from risk_brain.overfit_detector import detect_overfit_flags
from risk_brain.walk_forward import out_of_sample_passed


def review_metrics(
    metrics: dict,
    rules: dict | None = None,
    lookahead_review: dict | None = None,
) -> tuple[StrategyStatus, list[str]]:
    active_rules = rules or load_config("risk_rules").get("global", {})
    flags: list[str] = []
    if metrics.get("archived") or metrics.get("manual_status") == StrategyStatus.ARCHIVED.value:
        return StrategyStatus.ARCHIVED, ["Strategy is archived."]
    if lookahead_review and lookahead_review.get("has_lookahead_risk"):
        flags.append("Possible look-ahead or unsafe generated logic detected.")
    if _num(metrics, "max_drawdown", 1) > active_rules.get("max_drawdown_limit", 0.20):
        flags.append("Max drawdown exceeds configured limit.")
    if _num(metrics, "trade_count", 0) < active_rules.get("min_trades", 50):
        flags.append("Trade count below minimum reliability threshold.")
    if _num(metrics, "profit_factor", 0) < active_rules.get("min_profit_factor", 1.10):
        flags.append("Profit factor is weak.")
    if not out_of_sample_passed(metrics, active_rules.get("min_out_of_sample_score", 0.0)):
        flags.append("Out-of-sample result is poor.")
    if _num(metrics, "win_rate", 0) > 0.75 and abs(_num(metrics, "avg_loss", 0)) > _num(metrics, "avg_win", 0) * 2:
        flags.append("High win rate hides much larger average losses.")
    if _num(metrics, "fee_slippage_adjusted_return", 0) < active_rules.get(
        "min_fee_slippage_adjusted_return", 0.0
    ):
        flags.append("Fee/slippage-adjusted performance is negative.")
    flags.extend(_dry_run_divergence_flags(metrics, active_rules))
    flags.extend(detect_overfit_flags(metrics, active_rules))

    if flags:
        return StrategyStatus.REJECTED, flags
    if _approved_for_dry_run(metrics, active_rules):
        return StrategyStatus.APPROVED_FOR_DRY_RUN, ["Passed v1 dry-run approval gates. Live trading remains disabled."]
    if _num(metrics, "trade_count", 0) < active_rules.get("min_trades", 50) * 2:
        return StrategyStatus.WATCHLIST, ["Needs more trade history before paper approval."]
    return StrategyStatus.PAPER_ONLY, ["Passed v1 risk gate; paper-only by default."]


def _dry_run_divergence_flags(metrics: dict, rules: dict) -> list[str]:
    dry_run_return = metrics.get("dry_run_return", metrics.get("dry_run_total_return"))
    if dry_run_return is None:
        return []
    backtest_return = _num(metrics, "fee_slippage_adjusted_return", _num(metrics, "total_return", 0))
    denominator = max(abs(backtest_return), 0.01)
    divergence = abs(float(dry_run_return) - backtest_return) / denominator
    if divergence > rules.get("material_dry_run_divergence", 0.25):
        return [f"Backtest and dry-run diverge materially ({divergence:.2%})."]
    return []


def _approved_for_dry_run(metrics: dict, rules: dict) -> bool:
    return (
        _num(metrics, "trade_count", 0) >= rules.get("min_trades", 50) * 2
        and _num(metrics, "out_of_sample_return", 0) >= rules.get("min_out_of_sample_score", 0.0)
        and _num(metrics, "max_drawdown", 1) <= rules.get("max_drawdown_limit", 0.20)
        and _num(metrics, "profit_factor", 0) >= rules.get("min_profit_factor", 1.10)
        and _num(metrics, "fee_slippage_adjusted_return", 0)
        > rules.get("min_fee_slippage_adjusted_return", 0.0)
    )


def _num(metrics: dict, key: str, default: float) -> float:
    try:
        value = metrics.get(key, default)
        return float(value if value is not None else default)
    except (TypeError, ValueError):
        return default


def run_risk_reviews() -> list[dict]:
    rows = fetch_dataframe("SELECT * FROM backtest_metrics")
    reviews: list[dict] = []
    for _, row in rows.iterrows():
        metrics = row.to_dict()
        lookahead_review = _lookahead_review(row["strategy_id"])
        status, flags = review_metrics(metrics, lookahead_review=lookahead_review)
        if lookahead_review.get("issues"):
            flags.extend([f"Look-ahead audit: {issue}" for issue in lookahead_review["issues"]])
        if lookahead_review.get("warnings"):
            flags.extend([f"Look-ahead warning: {warning}" for warning in lookahead_review["warnings"]])
        if (lookahead_review.get("issues") or lookahead_review.get("warnings")) and lookahead_review.get(
            "inspected_paths"
        ):
            flags.extend(
                [
                    f"Look-ahead inspected path: {path}"
                    for path in sorted(set(str(path) for path in lookahead_review["inspected_paths"] if path))
                ]
            )
        execute("DELETE FROM risk_reviews WHERE run_id = ?", (row["run_id"],))
        review = {
            "review_id": f"risk_{row['run_id']}",
            "strategy_id": row["strategy_id"],
            "run_id": row["run_id"],
            "status": status.value,
            "flags": json.dumps(flags),
            "reviewed_at": utc_now(),
        }
        insert_dict("risk_reviews", review)
        reviews.append(review)
    return reviews


def _lookahead_review(strategy_id: str) -> dict:
    issues: list[str] = []
    warnings: list[str] = []
    inspected_paths: list[str] = []
    specs = fetch_dataframe("SELECT source_yaml, spec_path FROM strategy_specs WHERE strategy_id = ?", (strategy_id,))
    if not specs.empty:
        issues.extend(contains_forbidden_logic(str(specs.iloc[0]["source_yaml"])))
        spec_path = str(specs.iloc[0].get("spec_path") or "")
        if spec_path:
            inspected_paths.append(spec_path)
    generated = fetch_dataframe("SELECT code_path FROM generated_strategies WHERE strategy_id = ?", (strategy_id,))
    for _, row in generated.iterrows():
        path = Path(str(row["code_path"]))
        inspected_paths.append(str(path))
        if path.exists():
            code = path.read_text(encoding="utf-8")
            issues.extend(contains_forbidden_logic(code, analyze_python=True))
            ast_review = analyze_python_lookahead_risk(code, strict=True)
            issues.extend(ast_review["risk_patterns"])
            warnings.extend(ast_review["warnings"])
        else:
            warnings.append(f"Generated strategy file not found: {path}")
    return {
        "has_lookahead_risk": bool(issues),
        "issues": sorted(set(issues)),
        "warnings": sorted(set(warnings)),
        "inspected_paths": sorted(set(inspected_paths)),
    }
