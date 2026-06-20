from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any

import numpy as np
import pandas as pd

from ai_strategy_brain.strategy_spec_validator import load_strategy_spec
from core.config_loader import load_global_config
from core.database import execute, fetch_dataframe, initialize_database, insert_dict, new_id, utc_now
from core.paths import REPORTS_DIR, SRC_DIR, resolve_project_path
from feature_brain.feature_pipeline import build_features
from freqtrade_brain.dry_run_config_builder import build_dry_run_config
from freqtrade_brain.freqtrade_result_parser import parse_freqtrade_result
from freqtrade_brain.freqtrade_strategy_converter import class_name


def freqtrade_cli_available() -> bool:
    return shutil.which("freqtrade") is not None


def _series_condition(df: pd.DataFrame, condition: dict[str, Any]) -> pd.Series:
    left = df[condition["indicator"]]
    value = condition["value"]
    right = df[value] if isinstance(value, str) and value in df.columns else float(value)
    operator = condition["operator"]
    if operator == ">":
        return left > right
    if operator == ">=":
        return left >= right
    if operator == "<":
        return left < right
    if operator == "<=":
        return left <= right
    if operator == "==":
        return left == right
    if operator == "!=":
        return left != right
    raise ValueError(f"Unsupported operator: {operator}")


def _logic_mask(df: pd.DataFrame, block: dict[str, Any]) -> pd.Series:
    key = "all" if "all" in block else "any"
    masks = [_series_condition(df, condition) for condition in block[key]]
    if key == "all":
        return pd.concat(masks, axis=1).all(axis=1)
    return pd.concat(masks, axis=1).any(axis=1)


def fallback_backtest(spec: dict[str, Any], features: pd.DataFrame) -> dict[str, Any]:
    """Small deterministic spot-only research backtester for first-run validation."""
    trades: list[dict[str, Any]] = []
    equity_curve = [1.0]
    for pair in spec["pairs"]:
        df = features[features["symbol"] == pair].dropna().reset_index(drop=True)
        if df.empty:
            continue
        entry_mask = _logic_mask(df, spec["entry_logic"])
        exit_mask = _logic_mask(df, spec["exit_logic"])
        in_trade = False
        entry_price = 0.0
        entry_index = 0
        stop_loss = float(spec["risk"]["stop_loss"])
        take_profit = float(spec["risk"]["take_profit"])
        for index, row in df.iterrows():
            price = float(row["close"])
            if not in_trade and bool(entry_mask.iloc[index]):
                in_trade = True
                entry_price = price
                entry_index = index
                continue
            if not in_trade:
                continue
            trade_return = price / entry_price - 1
            should_exit = (
                bool(exit_mask.iloc[index])
                or trade_return <= stop_loss
                or trade_return >= take_profit
                or index - entry_index >= 96
            )
            if should_exit:
                adjusted = trade_return - 0.002
                trades.append(
                    {
                        "pair": pair,
                        "entry_index": entry_index,
                        "exit_index": index,
                        "return": trade_return,
                        "adjusted_return": adjusted,
                    }
                )
                equity_curve.append(equity_curve[-1] * (1 + adjusted))
                in_trade = False
    if not trades:
        return _empty_metrics()
    returns = np.array([trade["adjusted_return"] for trade in trades], dtype=float)
    wins = returns[returns > 0]
    losses = returns[returns < 0]
    gross_profit = float(wins.sum()) if len(wins) else 0.0
    gross_loss = abs(float(losses.sum())) if len(losses) else 0.0
    equity = np.array(equity_curve, dtype=float)
    running_max = np.maximum.accumulate(equity)
    drawdowns = equity / running_max - 1
    counts = pd.Series([trade["pair"] for trade in trades]).value_counts(normalize=True)
    midpoint = len(returns) // 2 or 1
    x = np.arange(len(equity))
    smoothness = abs(float(np.corrcoef(x, equity)[0, 1])) if len(equity) > 2 else 1.0
    return {
        "total_return": float(equity[-1] - 1),
        "out_of_sample_return": float(np.prod(1 + returns[midpoint:]) - 1),
        "max_drawdown": abs(float(drawdowns.min())),
        "sharpe": float(returns.mean() / returns.std() * np.sqrt(365)) if returns.std() else 0.0,
        "sortino": float(returns.mean() / losses.std() * np.sqrt(365)) if len(losses) and losses.std() else 0.0,
        "win_rate": float((returns > 0).mean()),
        "trade_count": int(len(trades)),
        "profit_factor": gross_profit / gross_loss if gross_loss else 99.0,
        "avg_profit": float(returns.mean()),
        "avg_win": float(wins.mean()) if len(wins) else 0.0,
        "avg_loss": float(losses.mean()) if len(losses) else 0.0,
        "best_pair": str(counts.index[0]) if not counts.empty else None,
        "worst_pair": str(counts.index[-1]) if not counts.empty else None,
        "pair_level_metrics": _fallback_pair_metrics(trades),
        "fee_adjusted_return": float(equity[-1] - 1),
        "slippage_adjusted_return": float(equity[-1] - 1),
        "fee_slippage_adjusted_return": float(equity[-1] - 1),
        "pair_concentration": float(counts.max()) if not counts.empty else 1.0,
        "regime_count": 2,
        "equity_smoothness": smoothness,
        "parser_warnings": ["internal research fallback metrics; not a Freqtrade CLI result"],
        "trade_sample": trades[:10],
    }


def _empty_metrics() -> dict[str, Any]:
    return {
        "total_return": 0.0,
        "out_of_sample_return": 0.0,
        "max_drawdown": 1.0,
        "sharpe": 0.0,
        "sortino": 0.0,
        "win_rate": 0.0,
        "trade_count": 0,
        "profit_factor": 0.0,
        "avg_profit": 0.0,
        "avg_win": 0.0,
        "avg_loss": 0.0,
        "best_pair": None,
        "worst_pair": None,
        "pair_level_metrics": {},
        "fee_adjusted_return": 0.0,
        "slippage_adjusted_return": 0.0,
        "fee_slippage_adjusted_return": 0.0,
        "pair_concentration": 1.0,
        "regime_count": 0,
        "equity_smoothness": 1.0,
        "parser_warnings": ["no trades produced metrics"],
        "trade_sample": [],
    }


def _fallback_pair_metrics(trades: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    metrics: dict[str, dict[str, Any]] = {}
    if not trades:
        return metrics
    for pair, group in pd.DataFrame(trades).groupby("pair"):
        returns = group["adjusted_return"]
        metrics[str(pair)] = {
            "total_return": float((1 + returns).prod() - 1),
            "trade_count": int(len(group)),
            "win_rate": float((returns > 0).mean()),
            "profit_factor": float(returns[returns > 0].sum() / abs(returns[returns < 0].sum()))
            if abs(returns[returns < 0].sum())
            else 99.0,
        }
    return metrics


def _spec_paths() -> list:
    runtime_paths = load_global_config().get("runtime_paths", {})
    directory = resolve_project_path(runtime_paths.get("generated_specs", "data/generated/specs"))
    paths = sorted(directory.glob("*.yaml")) if directory.exists() else []
    if paths:
        return paths
    return sorted((SRC_DIR / "ai_strategy_brain" / "generated_specs").glob("*.yaml"))


def run_backtests(use_freqtrade_cli: bool = False, strict: bool = False) -> list[dict[str, Any]]:
    initialize_database()
    specs = [load_strategy_spec(path) for path in _spec_paths()]
    specs = [spec for spec in specs if spec.get("engine_target") == "freqtrade"]
    if not specs:
        raise ValueError("No Freqtrade YAML specs found. Run generate_strategy_specs first.")
    try:
        features = fetch_dataframe("SELECT * FROM market_data ORDER BY symbol, timestamp")
        if features.empty:
            raise ValueError
        features = build_features()
    except Exception:
        features = build_features()

    results: list[dict[str, Any]] = []
    report_dir = REPORTS_DIR / "freqtrade"
    report_dir.mkdir(parents=True, exist_ok=True)
    for spec in specs:
        run_id = new_id("bt")
        started = utc_now()
        if use_freqtrade_cli and freqtrade_cli_available():
            try:
                metrics = _run_freqtrade_cli(spec, run_id)
                status = "completed_freqtrade_cli"
            except RuntimeError as exc:
                _record_failed_run(run_id, spec, started, str(exc))
                if strict:
                    raise
                results.append(
                    {
                        "run_id": run_id,
                        "strategy_id": spec["strategy_name"],
                        "status": "failed_freqtrade_cli",
                        "error": str(exc),
                    }
                )
                continue
        else:
            metrics = fallback_backtest(spec, features)
            status = "completed_internal_research_fallback"
        result_path = report_dir / f"{run_id}_{spec['strategy_name']}.json"
        result_path.write_text(json.dumps({"spec": spec, "metrics": metrics}, indent=2), encoding="utf-8")
        insert_dict(
            "backtest_runs",
            {
                "run_id": run_id,
                "strategy_id": spec["strategy_name"],
                "engine": "freqtrade_cli" if use_freqtrade_cli else "internal_research_fallback",
                "started_at": started,
                "completed_at": utc_now(),
                "status": status,
                "result_path": str(result_path),
                "notes": "Internal fallback is for research validation only." if not use_freqtrade_cli else "",
            },
        )
        store_metrics(run_id, spec["strategy_name"], metrics)
        results.append({"run_id": run_id, "strategy_id": spec["strategy_name"], **metrics})
    return results


def _run_freqtrade_cli(spec: dict[str, Any], run_id: str) -> dict[str, Any]:
    runtime_paths = load_global_config().get("runtime_paths", {})
    strategy_dir = resolve_project_path(
        runtime_paths.get("generated_freqtrade_strategies", "data/generated/freqtrade_strategies")
    )
    report_dir = resolve_project_path(runtime_paths.get("freqtrade_reports", "reports/freqtrade"))
    user_data_dir = resolve_project_path("data/freqtrade")
    report_dir.mkdir(parents=True, exist_ok=True)
    strategy = class_name(spec["strategy_name"])
    config_path = build_dry_run_config(spec.get("pairs", []))
    export_path = report_dir / f"{run_id}_{spec['strategy_name']}_freqtrade_export.json"
    command = [
        "freqtrade",
        "backtesting",
        "--userdir",
        str(user_data_dir),
        "--config",
        str(config_path),
        "--strategy",
        strategy,
        "--strategy-path",
        str(strategy_dir),
        "--timeframe",
        spec.get("timeframe", "1h"),
        "--export",
        "trades",
        "--export-filename",
        str(export_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(_safe_process_output(result))
    parse_path = export_path if export_path.exists() else _latest_export(report_dir, run_id)
    if parse_path is None:
        raise RuntimeError(
            "Freqtrade CLI completed but no export JSON was found. "
            f"Expected {export_path}. stdout: {_safe_process_output(result)}"
        )
    metrics = parse_freqtrade_result(parse_path, strategy)
    metrics["result_export_path"] = str(parse_path)
    return _metrics_with_defaults(metrics)


def _latest_export(report_dir, run_id: str):
    matches = sorted(report_dir.glob(f"*{run_id}*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def _safe_process_output(result: subprocess.CompletedProcess[str]) -> str:
    text = (result.stderr or result.stdout or "").strip()
    return text[-4000:] if text else f"Process exited with {result.returncode}."


def _metrics_with_defaults(metrics: dict[str, Any]) -> dict[str, Any]:
    empty = _empty_metrics()
    empty.update(metrics)
    empty["engine"] = metrics.get("engine", "freqtrade_cli")
    empty["pair_concentration"] = _pair_concentration(metrics.get("pair_level_metrics") or {})
    empty["regime_count"] = metrics.get("regime_count") or 0
    empty["equity_smoothness"] = metrics.get("equity_smoothness") or 0.0
    empty["out_of_sample_return"] = metrics.get("out_of_sample_return") or 0.0
    return empty


def _pair_concentration(pair_level_metrics: dict[str, Any]) -> float:
    if not pair_level_metrics:
        return 1.0
    trade_counts = [
        int((values or {}).get("trade_count") or 0)
        for values in pair_level_metrics.values()
        if isinstance(values, dict)
    ]
    total = sum(trade_counts)
    return max(trade_counts) / total if total else 1.0


def _record_failed_run(run_id: str, spec: dict[str, Any], started: str, message: str) -> None:
    insert_dict(
        "backtest_runs",
        {
            "run_id": run_id,
            "strategy_id": spec["strategy_name"],
            "engine": "freqtrade_cli",
            "started_at": started,
            "completed_at": utc_now(),
            "status": "failed_freqtrade_cli",
            "result_path": "",
            "notes": message,
        },
    )
    insert_dict(
        "engine_runs",
        {
            "engine_run_id": new_id("engine"),
            "engine": "freqtrade_cli",
            "command": "freqtrade backtesting",
            "status": "failed",
            "started_at": started,
            "completed_at": utc_now(),
            "output_path": "",
            "notes": message,
        },
    )


def store_metrics(run_id: str, strategy_id: str, metrics: dict[str, Any]) -> None:
    execute(
        """
        INSERT OR REPLACE INTO backtest_metrics
        (run_id, strategy_id, total_return, out_of_sample_return, max_drawdown, sharpe, sortino,
         win_rate, trade_count, profit_factor, avg_win, avg_loss, fee_slippage_adjusted_return,
         pair_concentration, regime_count, equity_smoothness, created_at, avg_profit, best_pair,
         worst_pair, pair_level_metrics, fee_adjusted_return, slippage_adjusted_return, parser_warnings)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            strategy_id,
            _float_metric(metrics, "total_return"),
            _float_metric(metrics, "out_of_sample_return"),
            _float_metric(metrics, "max_drawdown"),
            _float_metric(metrics, "sharpe"),
            _float_metric(metrics, "sortino"),
            _float_metric(metrics, "win_rate"),
            int(metrics.get("trade_count") or 0),
            _float_metric(metrics, "profit_factor"),
            _float_metric(metrics, "avg_win"),
            _float_metric(metrics, "avg_loss"),
            _float_metric(metrics, "fee_slippage_adjusted_return"),
            _float_metric(metrics, "pair_concentration"),
            int(metrics.get("regime_count") or 0),
            _float_metric(metrics, "equity_smoothness"),
            utc_now(),
            _float_metric(metrics, "avg_profit"),
            metrics.get("best_pair"),
            metrics.get("worst_pair"),
            json.dumps(metrics.get("pair_level_metrics") or {}),
            _float_metric(metrics, "fee_adjusted_return"),
            _float_metric(metrics, "slippage_adjusted_return"),
            json.dumps(metrics.get("parser_warnings") or []),
        ),
    )


def _float_metric(metrics: dict[str, Any], key: str) -> float:
    value = metrics.get(key)
    try:
        return float(value if value is not None else 0.0)
    except (TypeError, ValueError):
        return 0.0
