from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from ai.local_ai_client import get_local_ai_status
from core.config_loader import load_config
from core.database import fetch_dataframe
from lean_brain.lean_adapter import get_lean_status
from qlib_brain.qlib_adapter import get_qlib_status


STANDARD_RUN_COLUMNS = ["engine", "item_id", "status", "created_at", "report_path", "warning_summary", "error_summary"]
WARNING_SUMMARY_LIMIT = 240


def load_engine_registry() -> pd.DataFrame:
    """Load engine registry as a display DataFrame. No engine execution is performed."""
    try:
        registry = load_config("engine_registry").get("engines", {})
    except Exception:
        return pd.DataFrame(columns=["engine", "status", "safe_for_live", "execution_allowed", "requires_optional_package", "notes"])
    rows = []
    for engine, values in registry.items():
        values = values or {}
        rows.append(
            {
                "engine": engine,
                "status": values.get("status", "not verified"),
                "safe_for_live": values.get("safe_for_live", "not verified"),
                "execution_allowed": values.get("execution_allowed", "not verified"),
                "requires_optional_package": values.get("requires_optional_package", False),
                "notes": values.get("current_capability") or values.get("role") or "",
                "next_step": values.get("next_step", ""),
            }
        )
    return pd.DataFrame(rows)


def get_openbb_data_health() -> dict[str, Any]:
    """Return OpenBB local data health. Reads local DB only."""
    rows = _safe_fetch_dataframe(
        """
        SELECT symbol, provider, interval, COUNT(*) AS rows,
               MIN(timestamp) AS first_timestamp, MAX(timestamp) AS latest_timestamp
        FROM openbb_market_data
        GROUP BY symbol, provider, interval
        ORDER BY symbol, provider, interval
        """
    )
    duplicates = _safe_fetch_dataframe(
        """
        SELECT symbol, provider, interval, COUNT(*) AS duplicate_groups
        FROM (
            SELECT symbol, provider, interval, timestamp, COUNT(*) AS rows
            FROM openbb_market_data
            GROUP BY symbol, provider, interval, timestamp
            HAVING COUNT(*) > 1
        )
        GROUP BY symbol, provider, interval
        ORDER BY symbol, provider, interval
        """
    )
    return {
        "rows_by_symbol": rows,
        "duplicates": duplicates,
        "total_rows": int(rows["rows"].sum()) if not rows.empty and "rows" in rows else 0,
        "warnings": [] if rows.attrs.get("status") != "missing_table" else ["openbb_market_data table missing."],
    }


def get_latest_daily_runs(limit: int = 5) -> pd.DataFrame:
    return _summarize_run_frame(
        _safe_fetch_dataframe(
        """
        SELECT 'daily_research' AS engine, run_id AS item_id, status, started_at AS created_at,
               analytics_report_path AS report_path, warnings_json AS warning_summary,
               errors_json AS error_summary
        FROM daily_research_runs
        ORDER BY started_at DESC
        LIMIT ?
        """,
        (limit,),
        columns=STANDARD_RUN_COLUMNS,
        )
    )


def get_latest_ai_memos(limit: int = 5) -> pd.DataFrame:
    return _summarize_run_frame(
        _safe_fetch_dataframe(
        """
        SELECT 'local_ai' AS engine, memo_id AS item_id, status, created_at,
               metadata_json AS report_path, warnings_json AS warning_summary,
               '' AS error_summary
        FROM ai_research_memos
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
        columns=STANDARD_RUN_COLUMNS,
        )
    )


def get_latest_lean_runs(limit: int = 5) -> pd.DataFrame:
    return _summarize_run_frame(
        _safe_fetch_dataframe(
        """
        SELECT 'lean' AS engine, run_id AS item_id, status, created_at,
               report_path, warnings_json AS warning_summary, errors_json AS error_summary
        FROM lean_backtest_runs
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
        columns=STANDARD_RUN_COLUMNS,
        )
    )


def get_latest_qlib_runs(limit: int = 5) -> pd.DataFrame:
    return _summarize_run_frame(
        _safe_fetch_dataframe(
        """
        SELECT 'qlib' AS engine, run_id AS item_id, status, created_at,
               report_path, warnings_json AS warning_summary, errors_json AS error_summary
        FROM qlib_experiment_runs
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
        columns=STANDARD_RUN_COLUMNS,
        )
    )


def get_latest_qlib_exports(limit: int = 5) -> pd.DataFrame:
    return _summarize_run_frame(
        _safe_fetch_dataframe(
        """
        SELECT 'qlib_dataset' AS engine, export_id AS item_id, status, created_at,
               manifest_path AS report_path, warnings_json AS warning_summary, errors_json AS error_summary,
               row_count, feature_count, output_path
        FROM qlib_dataset_exports
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
        )
    )


def get_latest_openbb_ingestion_runs(limit: int = 5) -> pd.DataFrame:
    return _summarize_run_frame(
        _safe_fetch_dataframe(
        """
        SELECT 'openbb' AS engine, run_id AS item_id, status, started_at AS created_at,
               '' AS report_path, warnings_json AS warning_summary, errors_json AS error_summary
        FROM openbb_ingestion_runs
        ORDER BY started_at DESC
        LIMIT ?
        """,
        (limit,),
        columns=STANDARD_RUN_COLUMNS,
        )
    )


def build_latest_runs(limit: int = 5) -> pd.DataFrame:
    qlib_exports = get_latest_qlib_exports(limit)
    frames = [
        get_latest_daily_runs(limit),
        get_latest_ai_memos(limit),
        get_latest_lean_runs(limit),
        get_latest_qlib_runs(limit),
        qlib_exports[STANDARD_RUN_COLUMNS]
        if not qlib_exports.empty
        else pd.DataFrame(columns=STANDARD_RUN_COLUMNS),
        get_latest_openbb_ingestion_runs(limit),
    ]
    frames = [frame for frame in frames if frame is not None and not frame.empty]
    if not frames:
        return pd.DataFrame(columns=STANDARD_RUN_COLUMNS)
    return pd.concat(frames, ignore_index=True).sort_values("created_at", ascending=False, na_position="last")


def build_safety_checklist() -> pd.DataFrame:
    """Build a read-only safety checklist from local configs."""
    global_config = _load_config_safe("global")
    local_ai = _load_config_safe("local_ai")
    daily = _load_config_safe("daily_research")
    lean = _load_config_safe("lean")
    qlib = _load_config_safe("qlib")
    safety = global_config.get("safety", {})
    checks = [
        _check_false("OpenAI API disabled", local_ai.get("allow_openai_api")),
        _check_false("ChatGPT OAuth disabled", local_ai.get("allow_chatgpt_oauth")),
        _check_false("credentials disabled", _any_truthy([lean.get("allow_brokerage_credentials"), qlib.get("allow_cloud_credentials")])),
        _check_false("brokerage disabled", lean.get("allow_brokerage_credentials")),
        _check_false("live trading disabled", safety.get("live_trading_enabled")),
        _check_false("futures disabled", safety.get("futures_enabled")),
        _check_false("leverage disabled", safety.get("leverage_enabled")),
        _check_false("real orders disabled", safety.get("real_orders_enabled")),
        _check_false("Qlib daily disabled by default", daily.get("qlib", {}).get("enabled") or daily.get("qlib", {}).get("run_experiment")),
        _check_false("LEAN daily disabled by default", daily.get("lean", {}).get("enabled") or daily.get("lean", {}).get("run_backtest")),
    ]
    return pd.DataFrame(checks)


def build_next_actions() -> list[str]:
    """Return static rule-based next actions. No LLM or external calls are used."""
    actions: list[str] = []
    qlib_status = get_qlib_status()
    lean_status = get_lean_execution_summary()
    ai_status = get_local_ai_status({"timeout_seconds": 2})
    daily = get_latest_daily_runs(1)

    if not qlib_status.get("qlib_import_available"):
        actions.append("Qlib installed execution not verified; dataset export is available.")
    if not lean_status.get("cli_detected"):
        actions.append("LEAN CLI missing; skeleton/data export mode only.")
    if lean_status.get("status") in {"executable_failed_timeout", "cli_detected_executable_unverified"}:
        actions.append("LEAN executable backtest remains future Docker/runtime diagnostics.")
    if not ai_status.get("available"):
        actions.append("Local AI unavailable; start Ollama before running AI memo workflows.")
    if not daily.empty:
        actions.append("Latest daily pipeline DB run exists; Windows Task Scheduler state is not verified here.")
    actions.append("Manual UI check recommended after launching Streamlit.")
    return actions


def get_latest_engine_statuses() -> dict[str, Any]:
    """Return compact status cards for the control center."""
    openbb = get_openbb_data_health()
    daily = get_latest_daily_runs(1)
    qlib_status = get_qlib_status()
    lean_status = get_lean_execution_summary()
    ai_status = get_local_ai_status({"timeout_seconds": 2})
    checklist = build_safety_checklist()
    safety_ok = bool(not checklist.empty and (checklist["status"] == "safe").all())
    return {
        "openbb": {"status": "has_data" if openbb["total_rows"] else "no_data", "rows": openbb["total_rows"]},
        "local_ai": {"status": "available" if ai_status.get("available") else "unavailable", "model": ai_status.get("model")},
        "latest_daily_run": {
            "status": str(daily.iloc[0]["status"]) if not daily.empty else "not verified",
            "scheduler_state": "not_verified",
            "source": "daily_research_runs",
        },
        "lean": lean_status,
        "qlib": {"status": qlib_status.get("status"), "available": qlib_status.get("qlib_import_available"), "safe_for_live": False},
        "safety": {"status": "safe" if safety_ok else "not verified"},
    }


def get_lean_execution_summary() -> dict[str, Any]:
    """Summarize LEAN honestly: CLI/skeleton can exist while executable runs remain unverified."""
    status = get_lean_status()
    cli_detected = bool(status.get("lean_cli_available"))
    runs = _safe_fetch_dataframe(
        """
        SELECT run_id, status, command_text, warnings_json, errors_json, created_at
        FROM lean_backtest_runs
        ORDER BY created_at DESC
        LIMIT 20
        """,
        columns=["run_id", "status", "command_text", "warnings_json", "errors_json", "created_at"],
    )
    skeleton_available = cli_detected or not runs.empty
    latest_executable_status = "not_verified"
    latest_executable_run_id = ""
    executable_verified = False
    card_status = "cli_detected_executable_unverified" if cli_detected else "missing"

    if not runs.empty:
        executable_runs = runs[runs["command_text"].fillna("").astype(str).str.strip() != ""]
        if not executable_runs.empty:
            latest = executable_runs.iloc[0]
            latest_executable_status = str(latest.get("status") or "not_verified")
            latest_executable_run_id = str(latest.get("run_id") or "")
            all_statuses = {str(value).lower() for value in executable_runs["status"].fillna("")}
            executable_verified = "completed" in all_statuses or "completed_with_warnings" in all_statuses
            combined_messages = " ".join(
                str(latest.get(column) or "") for column in ("warnings_json", "errors_json")
            ).lower()
            if executable_verified:
                card_status = "executable_completed"
            elif (
                "timeout" in combined_messages
                or "timed out" in combined_messages
                or latest_executable_status.lower() == "timeout"
            ):
                card_status = "executable_failed_timeout"
            elif latest_executable_status.lower() in {"failed", "unavailable", "partial_failed"}:
                card_status = "cli_detected_executable_unverified"

    return {
        "status": card_status,
        "cli_detected": cli_detected,
        "skeleton_available": skeleton_available,
        "executable_verified": executable_verified,
        "latest_executable_status": latest_executable_status,
        "latest_executable_run_id": latest_executable_run_id,
        "safe_for_live": False,
    }


def summarize_text(value: Any, limit: int = WARNING_SUMMARY_LIMIT) -> str:
    """Compact warning/error text for dashboards and reports without hiding that details exist."""
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    if isinstance(value, (dict, list, tuple)):
        text = json.dumps(value, ensure_ascii=True, default=str)
    else:
        raw = str(value)
        if not raw or raw.lower() == "nan":
            return ""
        try:
            text = json.dumps(json.loads(raw), ensure_ascii=True, default=str)
        except Exception:
            text = raw
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def _summarize_run_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    for column in ("warning_summary", "error_summary"):
        if column in df.columns:
            df[column] = df[column].map(summarize_text)
    return df


def _safe_fetch_dataframe(query: str, params: tuple[Any, ...] = (), columns: list[str] | None = None) -> pd.DataFrame:
    try:
        return fetch_dataframe(query, params)
    except Exception as exc:
        if _is_missing_table_error(exc):
            df = pd.DataFrame(columns=columns or [])
            df.attrs["status"] = "missing_table"
            df.attrs["warning"] = str(exc)
            return df
        raise


def _is_missing_table_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "no such table" in message or "does not exist" in message or "not found" in message or "catalog error" in message


def _load_config_safe(name: str) -> dict[str, Any]:
    try:
        return load_config(name)
    except Exception:
        return {}


def _check_false(label: str, value: Any) -> dict[str, str]:
    if value is False:
        return {"check": label, "status": "safe", "value": "false"}
    if value is True:
        return {"check": label, "status": "unsafe", "value": "true"}
    if value in (None, ""):
        return {"check": label, "status": "not verified", "value": str(value)}
    return {"check": label, "status": "safe" if not bool(value) else "unsafe", "value": str(value)}


def _any_truthy(values: list[Any]) -> bool:
    return any(bool(value) for value in values)


def _markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    columns = [str(column) for column in df.columns]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[column]).replace("\n", " ") for column in df.columns) + " |")
    return "\n".join(lines)


def write_control_center_report(output_dir: str | Path | None = None) -> dict[str, Any]:
    """Write a compact markdown status report without running engines."""
    from core.database import utc_now
    from core.paths import REPORTS_DIR, resolve_project_path

    root = resolve_project_path(output_dir or REPORTS_DIR / "control_center")
    root.mkdir(parents=True, exist_ok=True)
    timestamp = utc_now().replace(":", "").replace("+", "_")
    path = root / f"control_center_status_{timestamp}.md"
    statuses = get_latest_engine_statuses()
    checklist = build_safety_checklist()
    actions = build_next_actions()
    body = [
        "# Research Control Center Status",
        "",
        "Research-only status report. No engines were executed.",
        "",
        "## Engine Statuses",
        "```json",
        json.dumps(statuses, indent=2, default=str),
        "```",
        "",
        "## Safety Checklist",
        _markdown_table(checklist) if not checklist.empty else "No checklist rows.",
        "",
        "## Next Actions",
        *[f"- {action}" for action in actions],
    ]
    path.write_text("\n".join(body), encoding="utf-8")
    return {"report_path": str(path), "statuses": statuses, "actions": actions}
