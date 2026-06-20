from __future__ import annotations

import importlib.util
import json
import platform
import sys
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from ai.research_engine import run_local_ai_research
from analytics.openbb_analytics import (
    compute_openbb_data_quality,
    compute_openbb_pair_comparison,
    compute_openbb_return_summary,
    load_openbb_prices,
)
from core.config_loader import load_config, load_yaml
from core.database import fetch_dataframe, initialize_database, insert_dict, new_id, utc_now
from core.paths import REPORTS_DIR, resolve_project_path
from core.validation import assert_research_only
from data_brain.openbb_adapter import ingest_openbb_market_data


@dataclass
class DailyResearchResult:
    run_id: str
    status: str
    symbols: list[str]
    provider: str
    interval: str
    openbb_ingestion_run_id: str | None = None
    analytics_report_path: str | None = None
    local_ai_memo_id: str | None = None
    local_ai_report_path: str | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    started_at: str = ""
    finished_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_daily_research_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load daily research config from the project config directory or an explicit path."""
    return load_yaml(path) if path else load_config("daily_research")


def run_daily_research_pipeline(
    symbols: list[str] | None = None,
    provider: str | None = None,
    interval: str | None = None,
    start_date: str | None = None,
    task_type: str | None = None,
    model: str | None = None,
    skip_ingest: bool = False,
    skip_ai: bool = False,
    dry_run: bool = False,
    config: dict[str, Any] | None = None,
) -> DailyResearchResult:
    """Run the local research-only daily pipeline and persist run metadata."""
    assert_research_only(load_config("global"))
    active = config or load_daily_research_config()
    initialize_database()

    run_id = new_id("daily")
    started_at = utc_now()
    selected_symbols = symbols or list(active.get("default_symbols", ["AAPL", "MSFT"]))
    selected_provider = provider or str(active.get("provider", "yfinance"))
    selected_interval = interval or str(active.get("interval", "1d"))
    selected_start = start_date or str(active.get("start_date", "2022-01-01"))
    selected_task = task_type or str(active.get("task_type", "daily_research_note"))
    selected_model = model or str(active.get("local_ai", {}).get("model", "qwen2.5:3b"))
    asset_class = str(active.get("asset_class", "equity"))
    result = DailyResearchResult(
        run_id=run_id,
        status="running",
        symbols=selected_symbols,
        provider=selected_provider,
        interval=selected_interval,
        started_at=started_at,
    )
    metadata = {
        "dry_run": dry_run,
        "skip_ingest": skip_ingest,
        "skip_ai": skip_ai,
        "asset_class": asset_class,
        "start_date": selected_start,
        "task_type": selected_task,
        "model": selected_model,
        "environment": _environment_diagnostics(selected_model),
        "fresh_openbb_ingestion_attempted": False,
        "fresh_openbb_ingestion_status": "skipped",
        "existing_openbb_rows_used": 0,
    }

    try:
        if dry_run:
            result.warnings.append("Dry run only: no OpenBB ingestion or Local AI call executed.")
        elif not skip_ingest:
            metadata["fresh_openbb_ingestion_attempted"] = True
            ingestion = ingest_openbb_market_data(
                symbols=selected_symbols,
                asset_class=asset_class,
                start_date=selected_start,
                interval=selected_interval,
                provider=selected_provider,
                write_db=True,
                write_parquet=True,
            )
            result.openbb_ingestion_run_id = ingestion.run_id
            metadata["fresh_openbb_ingestion_status"] = ingestion.status
            metadata["fresh_openbb_ingestion_rows_inserted"] = int(getattr(ingestion, "rows_inserted", 0))
            metadata["fresh_openbb_ingestion_rows_failed"] = int(getattr(ingestion, "rows_failed", 0))
            metadata["fresh_openbb_ingestion_rows_skipped_duplicate"] = int(
                getattr(ingestion, "rows_skipped_duplicate", 0)
            )
            metadata["fresh_openbb_ingestion_rows_updated"] = int(getattr(ingestion, "rows_updated", 0))
            metadata["fresh_openbb_ingestion_dedupe_enabled"] = bool(getattr(ingestion, "dedupe_enabled", True))
            result.warnings.extend(ingestion.warnings)
            result.errors.extend(ingestion.errors)
            if ingestion.status not in {"completed", "completed_with_warnings"}:
                result.warnings.append(f"OpenBB ingestion status: {ingestion.status}")

        analytics_paths = _write_analytics_reports(run_id, selected_symbols, selected_provider, selected_interval)
        result.analytics_report_path = analytics_paths.get("markdown") or analytics_paths.get("csv")
        metadata["analytics_paths"] = analytics_paths
        metadata["existing_openbb_rows_used"] = _openbb_row_count(selected_symbols, selected_provider, selected_interval)

        if dry_run:
            result.status = "dry_run"
        elif skip_ai:
            result.warnings.append("Local AI step skipped by request.")
            result.status = "completed_with_warnings" if result.warnings else "completed"
        else:
            local_ai_config = load_config("local_ai")
            local_ai_config.update(active.get("local_ai", {}))
            local_ai_config["model"] = selected_model
            local_ai_config["base_url"] = str(active.get("local_ai", {}).get("base_url", local_ai_config.get("base_url")))
            ai_result = run_local_ai_research(
                symbols=selected_symbols,
                provider=selected_provider,
                interval=selected_interval,
                task_type=selected_task,
                include_openbb=bool(active.get("include_sections", {}).get("openbb", True)),
                include_backtests=bool(active.get("include_sections", {}).get("backtests", True)),
                include_risk=bool(active.get("include_sections", {}).get("risk", True)),
                include_decisions=bool(active.get("include_sections", {}).get("decisions", True)),
                config=local_ai_config,
            )
            result.local_ai_memo_id = ai_result.get("memo_id")
            result.local_ai_report_path = ai_result.get("output_path")
            preflight = ai_result.get("preflight") or {}
            metadata["local_ai_preflight_status"] = preflight.get("status", "not_available")
            metadata["local_ai_model_available"] = bool(ai_result.get("model_available", False))
            metadata["local_ai_retry_attempts_used"] = int(ai_result.get("retry_attempts_used", 0) or 0)
            metadata["local_ai_compact_retry_used"] = bool(ai_result.get("compact_retry_used", False))
            metadata["local_ai_status"] = ai_result.get("local_ai_status") or ai_result.get("status")
            metadata["local_ai_error"] = ai_result.get("error")
            result.warnings.extend(ai_result.get("warnings", []))
            if ai_result.get("status") == "completed":
                result.status = "completed_with_warnings" if result.warnings or result.errors else "completed"
            else:
                result.status = "partial_failed"
                if ai_result.get("error"):
                    result.errors.append(str(ai_result["error"]))
        if result.errors and result.status in {"running", "completed", "completed_with_warnings"}:
            result.status = "partial_failed"
        elif result.status == "running":
            result.status = "completed_with_warnings" if result.warnings else "completed"
    except Exception as exc:
        result.status = "failed"
        result.errors.append(f"{type(exc).__name__}: {exc}")
    finally:
        result.finished_at = utc_now()
        _record_daily_research_run(result, selected_task, metadata)
    return result


def _write_analytics_reports(run_id: str, symbols: list[str], provider: str, interval: str) -> dict[str, str]:
    prices = load_openbb_prices(symbols=symbols, provider=provider, interval=interval)
    summary = compute_openbb_return_summary(prices)
    quality = compute_openbb_data_quality(prices)
    comparison = compute_openbb_pair_comparison(prices)
    output_dir = resolve_project_path(REPORTS_DIR / "daily_research" / run_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}

    csv_path = output_dir / "openbb_summary.csv"
    summary.to_csv(csv_path, index=False)
    paths["csv"] = str(csv_path)

    json_path = output_dir / "daily_research_summary.json"
    payload = {
        "run_id": run_id,
        "symbols": symbols,
        "provider": provider,
        "interval": interval,
        "return_summary": _records(summary),
        "data_quality": _quality_to_dict(quality),
        "correlation_matrix": _frame_to_nested_dict(comparison["correlation_matrix"]),
    }
    json_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    paths["json"] = str(json_path)

    md_path = output_dir / "daily_research_summary.md"
    md_path.write_text(_analytics_markdown(payload), encoding="utf-8")
    paths["markdown"] = str(md_path)
    return paths


def _environment_diagnostics(model: str) -> dict[str, Any]:
    return {
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "openbb_installed": importlib.util.find_spec("openbb") is not None,
        "ollama_available": _ollama_available(),
        "model_requested": model,
    }


def _ollama_available() -> bool:
    try:
        urllib.request.urlopen("http://localhost:11434/api/version", timeout=5).read()
    except Exception:
        return False
    return True


def _openbb_row_count(symbols: list[str], provider: str, interval: str) -> int:
    if not symbols:
        return 0
    placeholders = ", ".join(["?"] * len(symbols))
    try:
        rows = fetch_dataframe(
            f"""
            SELECT COUNT(*) AS rows
            FROM openbb_market_data
            WHERE symbol IN ({placeholders}) AND provider = ? AND interval = ?
            """,
            tuple([*symbols, provider, interval]),
        )
    except Exception:
        return 0
    return int(rows.iloc[0]["rows"]) if not rows.empty else 0


def _record_daily_research_run(result: DailyResearchResult, task_type: str, metadata: dict[str, Any]) -> None:
    insert_dict(
        "daily_research_runs",
        {
            "run_id": result.run_id,
            "started_at": result.started_at,
            "finished_at": result.finished_at,
            "status": result.status,
            "symbols": json.dumps(result.symbols),
            "provider": result.provider,
            "interval": result.interval,
            "task_type": task_type,
            "openbb_ingestion_run_id": result.openbb_ingestion_run_id,
            "analytics_report_path": result.analytics_report_path,
            "local_ai_memo_id": result.local_ai_memo_id,
            "local_ai_report_path": result.local_ai_report_path,
            "warnings_json": json.dumps(result.warnings),
            "errors_json": json.dumps(result.errors),
            "metadata_json": json.dumps(metadata),
        },
    )


def _records(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df is None or df.empty:
        return []
    return json.loads(df.to_json(orient="records", date_format="iso"))


def _quality_to_dict(quality: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in quality.items():
        result[key] = _records(value) if isinstance(value, pd.DataFrame) else value
    return result


def _frame_to_nested_dict(df: pd.DataFrame) -> dict[str, Any]:
    if df is None or df.empty:
        return {}
    return json.loads(df.to_json())


def _analytics_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# Daily Research Summary: {payload['run_id']}",
        "",
        "- Research-only automation. No orders were placed.",
        f"- Symbols: {', '.join(payload['symbols'])}",
        f"- Provider: {payload['provider']}",
        f"- Interval: {payload['interval']}",
        "",
        "## Return Summary",
        "",
    ]
    if payload["return_summary"]:
        lines.append("| Symbol | Rows | Latest Close | Total Return | Max Drawdown |")
        lines.append("|---|---:|---:|---:|---:|")
        for row in payload["return_summary"]:
            lines.append(
                "| {symbol} | {rows} | {latest_close} | {total_return} | {max_drawdown} |".format(
                    symbol=row.get("symbol", ""),
                    rows=row.get("rows", ""),
                    latest_close=row.get("latest_close", ""),
                    total_return=row.get("total_return", ""),
                    max_drawdown=row.get("max_drawdown", ""),
                )
            )
    else:
        lines.append("No local OpenBB summary rows were available.")
    lines.extend(
        [
            "",
            "## Data Quality",
            "",
            "```json",
            json.dumps(payload["data_quality"], indent=2, default=str),
            "```",
        ]
    )
    return "\n".join(lines)
