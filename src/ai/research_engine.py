from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from ai.local_ai_client import generate_with_local_ai, get_local_ai_status
from analytics.openbb_analytics import (
    compute_openbb_data_quality,
    compute_openbb_pair_comparison,
    compute_openbb_return_summary,
    load_openbb_prices,
)
from core.config_loader import load_config
from core.database import fetch_dataframe, insert_dict, new_id, utc_now
from core.logger import get_logger
from core.paths import REPORTS_DIR, resolve_project_path


ALLOWED_TASKS = {"market_review", "strategy_review", "risk_review", "daily_research_note"}
logger = get_logger(__name__)


def build_research_context(
    symbols: list[str] | None = None,
    provider: str | None = None,
    interval: str | None = None,
    task_type: str = "market_review",
    include_openbb: bool = True,
    include_backtests: bool = False,
    include_risk: bool = False,
    include_decisions: bool = False,
    max_context_chars: int | None = None,
) -> tuple[dict[str, Any], str]:
    """Build a local-only research context from database rows and analytics helpers."""
    task = _validate_task(task_type)
    context: dict[str, Any] = {
        "task_type": task,
        "symbols": symbols or [],
        "provider": provider,
        "interval": interval,
        "generated_at": utc_now(),
        "data_sources": [],
        "warnings": [],
    }

    if include_openbb:
        prices = load_openbb_prices(symbols=symbols, provider=provider, interval=interval)
        summary = compute_openbb_return_summary(prices)
        quality = compute_openbb_data_quality(prices)
        comparison = compute_openbb_pair_comparison(prices)
        context["data_sources"].append("openbb_market_data")
        context["openbb"] = {
            "row_count": int(len(prices)),
            "return_summary": _records(summary),
            "data_quality": _quality_to_dict(quality),
            "correlation_matrix": _frame_to_nested_dict(comparison["correlation_matrix"]),
        }
        if prices.empty:
            context["warnings"].append("No local OpenBB market rows found for the requested filters.")

    if include_backtests:
        context["data_sources"].append("backtest_metrics")
        context["backtests"] = _records(
            _safe_fetch(
                """
                SELECT *
                FROM backtest_metrics
                ORDER BY created_at DESC
                LIMIT 10
                """,
                "backtest_metrics",
                context["warnings"],
            )
        )
    if include_risk:
        context["data_sources"].append("risk_reviews")
        context["risk_reviews"] = _records(
            _safe_fetch(
                """
                SELECT *
                FROM risk_reviews
                ORDER BY reviewed_at DESC
                LIMIT 10
                """,
                "risk_reviews",
                context["warnings"],
            )
        )
    if include_decisions:
        context["data_sources"].append("decisions")
        context["decisions"] = _records(
            _safe_fetch(
                """
                SELECT *
                FROM decisions
                ORDER BY created_at DESC
                LIMIT 20
                """,
                "decisions",
                context["warnings"],
            )
        )

    markdown = _context_to_markdown(context)
    limit = max_context_chars if max_context_chars is not None else int(_load_local_ai_config().get("max_context_chars", 24000))
    if len(markdown) > limit:
        context["warnings"].append(f"Context markdown truncated to {limit} characters.")
        markdown = markdown[:limit] + "\n\n[Context truncated]\n"
    return context, markdown


def build_local_ai_prompt(context_markdown: str, task_type: str = "market_review") -> str:
    """Build a constrained prompt for descriptive local research analysis only."""
    task = _validate_task(task_type)
    return f"""You are a local-only trading research analyst.

Analyze only the provided local data. Distinguish facts, assumptions, and missing data.
Do not give direct buy or sell orders. Do not provide execution instructions.
Do not treat backtests as proof of future profit.
Explain data quality problems and uncertainty.
This is research analysis, not trading advice.

Task type: {task}

Return a concise markdown memo with these sections:
1. Executive summary
2. Market observations
3. Risk notes
4. Strategy/backtest interpretation if available
5. What to monitor next
6. Limitations

Local context:

{context_markdown}
"""


def run_local_ai_research(
    symbols: list[str] | None = None,
    provider: str | None = None,
    interval: str | None = None,
    task_type: str = "market_review",
    include_openbb: bool = True,
    include_backtests: bool = False,
    include_risk: bool = False,
    include_decisions: bool = False,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build context, run local AI if available, and persist the research memo locally."""
    active_config = _load_local_ai_config(config)
    task = _validate_task(task_type)
    context, context_markdown = build_research_context(
        symbols=symbols,
        provider=provider,
        interval=interval,
        task_type=task,
        include_openbb=include_openbb,
        include_backtests=include_backtests,
        include_risk=include_risk,
        include_decisions=include_decisions,
        max_context_chars=int(active_config.get("max_context_chars", 24000)),
    )
    prompt = build_local_ai_prompt(context_markdown, task)
    status = get_local_ai_status(active_config)
    warnings = list(context.get("warnings", []))
    if not status.get("available"):
        generation = {
            "status": "unavailable",
            "response_text": "",
            "error": status.get("error") or "Local AI unavailable.",
            "provider": status.get("provider", active_config.get("provider", "ollama")),
            "model": status.get("model", active_config.get("model", "llama3.1:8b")),
            "elapsed_seconds": 0,
        }
        warnings.append(str(generation["error"]))
    else:
        generation = generate_with_local_ai(prompt, active_config)
        compact_retry_used = False
        if generation.get("status") != "ok" and _should_try_compact_retry(str(generation.get("error") or "")):
            compact_prompt = build_local_ai_prompt(_compact_context_markdown(context), task)
            compact_generation = generate_with_local_ai(compact_prompt, active_config)
            compact_generation["compact_retry_used"] = True
            compact_generation["initial_error"] = generation.get("error")
            compact_generation["initial_retry_attempts_used"] = generation.get("retry_attempts_used", 0)
            generation = compact_generation
            prompt = compact_prompt
            compact_retry_used = True
        else:
            generation["compact_retry_used"] = False
        if generation.get("error"):
            warnings.append(str(generation["error"]))
        if compact_retry_used:
            warnings.append("Local AI compact retry was used after an initial transient generation failure.")

    memo_id = new_id("memo")
    created_at = utc_now()
    response_text = str(generation.get("response_text") or "")
    memo_status = "completed" if generation.get("status") == "ok" else "failed"
    output_path = _write_memo_file(memo_id, task, response_text, prompt, memo_status)
    row = {
        "memo_id": memo_id,
        "created_at": created_at,
        "provider": str(generation.get("provider") or active_config.get("provider", "ollama")),
        "model": str(generation.get("model") or active_config.get("model", "llama3.1:8b")),
        "task_type": task,
        "symbols": json.dumps(symbols or []),
        "source_context_json": _json_dumps(context),
        "prompt_text": prompt,
        "response_text": response_text,
        "status": memo_status,
        "warnings_json": json.dumps(warnings),
        "metadata_json": json.dumps(
            {
                "output_path": str(output_path),
                "elapsed_seconds": generation.get("elapsed_seconds"),
                "error": generation.get("error"),
                "preflight": generation.get("preflight"),
                "retry_attempts_used": generation.get("retry_attempts_used", 0),
                "compact_retry_used": generation.get("compact_retry_used", False),
                "initial_error": generation.get("initial_error"),
            }
        ),
    }
    insert_dict("ai_research_memos", row)
    return {
        "memo_id": memo_id,
        "status": memo_status,
        "provider": row["provider"],
        "model": row["model"],
        "task_type": task,
        "symbols": symbols or [],
        "output_path": str(output_path),
        "warnings": warnings,
        "error": generation.get("error"),
        "preflight": generation.get("preflight"),
        "retry_attempts_used": generation.get("retry_attempts_used", 0),
        "compact_retry_used": generation.get("compact_retry_used", False),
        "local_ai_status": generation.get("status"),
        "model_available": (generation.get("preflight") or {}).get("model_available"),
    }


def _load_local_ai_config(config: dict[str, Any] | None = None) -> dict[str, Any]:
    if config is not None:
        return config
    return load_config("local_ai")


def _validate_task(task_type: str) -> str:
    if task_type not in ALLOWED_TASKS:
        raise ValueError(f"Unsupported local AI task_type: {task_type}")
    return task_type


def _safe_fetch(query: str, table_name: str, warnings: list[str] | None = None) -> pd.DataFrame:
    try:
        return fetch_dataframe(query)
    except Exception as exc:
        if _is_missing_optional_table_error(exc, table_name):
            message = f"Optional context table missing: {table_name}"
            logger.warning(message)
            if warnings is not None:
                warnings.append(message)
            return pd.DataFrame()
        raise


def _is_missing_optional_table_error(exc: Exception, table_name: str) -> bool:
    message = str(exc).lower()
    table = table_name.lower()
    return table in message and (
        "no such table" in message
        or "does not exist" in message
        or "not found" in message
        or "catalog error" in message
    )


def _records(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df is None or df.empty:
        return []
    safe = df.copy()
    for column in safe.columns:
        if pd.api.types.is_datetime64_any_dtype(safe[column]):
            safe[column] = safe[column].astype(str)
    return json.loads(safe.to_json(orient="records", date_format="iso"))


def _quality_to_dict(quality: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in quality.items():
        if isinstance(value, pd.DataFrame):
            result[key] = _records(value)
        else:
            result[key] = value
    return result


def _frame_to_nested_dict(df: pd.DataFrame) -> dict[str, Any]:
    if df is None or df.empty:
        return {}
    return json.loads(df.to_json())


def _context_to_markdown(context: dict[str, Any]) -> str:
    return "```json\n" + _json_dumps(context) + "\n```"


def _compact_context_markdown(context: dict[str, Any]) -> str:
    openbb = context.get("openbb") or {}
    compact = {
        "task_type": context.get("task_type"),
        "symbols": context.get("symbols", []),
        "provider": context.get("provider"),
        "interval": context.get("interval"),
        "generated_at": context.get("generated_at"),
        "warnings": context.get("warnings", []),
        "openbb": {
            "row_count": openbb.get("row_count", 0),
            "return_summary": [
                {
                    "symbol": row.get("symbol"),
                    "rows": row.get("rows"),
                    "first_date": row.get("first_date"),
                    "last_date": row.get("last_date"),
                    "latest_close": row.get("latest_close"),
                    "total_return": row.get("total_return"),
                    "max_drawdown": row.get("max_drawdown"),
                }
                for row in openbb.get("return_summary", [])
            ],
            "data_quality": openbb.get("data_quality", {}),
        },
        "backtest_count": len(context.get("backtests", [])),
        "risk_review_count": len(context.get("risk_reviews", [])),
        "decision_count": len(context.get("decisions", [])),
    }
    return "```json\n" + _json_dumps(compact) + "\n```"


def _should_try_compact_retry(error: str) -> bool:
    text = error.lower()
    return any(token in text for token in ["remotedisconnected", "connectionreseterror", "timeouterror", "urlerror", "timed out", "closed connection"])


def _json_dumps(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, default=str)


def _write_memo_file(memo_id: str, task_type: str, response_text: str, prompt: str, status: str) -> Path:
    directory = resolve_project_path(REPORTS_DIR / "local_ai")
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{memo_id}_{task_type}.md"
    body = [
        f"# Local AI Research Memo: {memo_id}",
        "",
        f"- Status: {status}",
        "- Research only. Not trading advice. No orders were placed.",
        "",
        "## Response",
        "",
        response_text if response_text.strip() else "_No response generated._",
        "",
        "## Prompt",
        "",
        "```text",
        prompt,
        "```",
    ]
    path.write_text("\n".join(body), encoding="utf-8")
    return path
