from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.database import fetch_dataframe, initialize_database  # noqa: E402
from dashboard.components.tables import dataframe_or_message  # noqa: E402
from dashboard.components.ui import caveat_box, compact_dataframe, hero, metric_card, section_header, setup_page  # noqa: E402
from pipeline.daily_research_pipeline import run_daily_research_pipeline  # noqa: E402


def _symbols_label(value) -> str:
    if not value:
        return "none"
    try:
        parsed = json.loads(str(value))
        return ",".join(parsed)
    except Exception:
        return str(value)


def _show_json_field(label: str, value) -> None:
    with st.expander(label, expanded=False):
        try:
            st.json(json.loads(str(value or "[]")))
        except Exception:
            st.code(str(value))


def _metadata(value) -> dict:
    try:
        parsed = json.loads(str(value or "{}"))
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


initialize_database()
setup_page()
hero(
    "Daily Research",
    "Refresh local research data, analytics, and an optional local AI memo in one controlled workflow.",
    badges=[("Research automation", "info"), ("Local model", "neutral"), ("No orders", "success")],
)
caveat_box("The status below is the latest database run. It does not prove that Windows Task Scheduler is currently active.", "warning")

runs = fetch_dataframe(
    """
    SELECT run_id, started_at, finished_at, status, symbols, provider, interval, task_type,
           openbb_ingestion_run_id, analytics_report_path, local_ai_memo_id,
           local_ai_report_path, warnings_json, errors_json, metadata_json
    FROM daily_research_runs
    ORDER BY started_at DESC
    LIMIT 25
    """
)
latest = runs.iloc[0].to_dict() if not runs.empty else {}

cols = st.columns(5)
with cols[0]: metric_card("Latest Status", latest.get("status", "none"), ("DB run", "info"))
with cols[1]: metric_card("Symbols", _symbols_label(latest.get("symbols")), ("Universe", "neutral"))
with cols[2]: metric_card("Provider", latest.get("provider", "none"), ("Local ingest", "neutral"))
with cols[3]: metric_card("Memo", latest.get("local_ai_memo_id", "none"), ("Local AI", "success" if latest.get("local_ai_memo_id") else "warning"))
with cols[4]: metric_card("Interval", latest.get("interval", "none"), ("Research data", "neutral"))

section_header("Run Daily Research", "A local research workflow; never an execution workflow")
with st.form("daily_research_form"):
    symbols_text = st.text_input("Symbols", value="AAPL MSFT")
    provider = st.text_input("Provider", value="yfinance")
    interval = st.text_input("Interval", value="1d")
    start_date = st.text_input("Start date", value="2022-01-01")
    task_type = st.text_input("Task type", value="daily_research_note")
    model = st.text_input("Local model", value="qwen2.5:3b")
    skip_ingest = st.checkbox("Skip OpenBB ingest", value=False)
    skip_ai = st.checkbox("Skip Local AI", value=False)
    run_now = st.form_submit_button("Run daily research now")

if run_now:
    result = run_daily_research_pipeline(
        symbols=[part.strip() for part in symbols_text.split() if part.strip()],
        provider=provider.strip() or None,
        interval=interval.strip() or None,
        start_date=start_date.strip() or None,
        task_type=task_type.strip() or None,
        model=model.strip() or None,
        skip_ingest=skip_ingest,
        skip_ai=skip_ai,
    )
    st.success(f"Daily research run saved: {result.run_id} ({result.status})")
    if result.warnings:
        st.warning("; ".join(result.warnings))
    if result.errors:
        st.error("; ".join(result.errors))

with st.expander("Daily research run history", expanded=False):
    compact_dataframe(runs, height=320, empty_message="No daily research runs recorded yet.")

if latest:
    section_header("Latest Run Details")
    metadata = _metadata(latest.get("metadata_json"))
    st.write(
        {
            "run_id": latest.get("run_id"),
            "analytics_report_path": latest.get("analytics_report_path"),
            "local_ai_report_path": latest.get("local_ai_report_path"),
            "openbb_ingestion_run_id": latest.get("openbb_ingestion_run_id"),
        }
    )
    metric_cols = st.columns(4)
    with metric_cols[0]: metric_card("OpenBB Inserted", metadata.get("fresh_openbb_ingestion_rows_inserted", "n/a"), ("Fresh rows", "info"))
    with metric_cols[1]: metric_card("Duplicates Skipped", metadata.get("fresh_openbb_ingestion_rows_skipped_duplicate", "n/a"), ("Dedupe", "success"))
    with metric_cols[2]: metric_card("AI Retries", metadata.get("local_ai_retry_attempts_used", "n/a"), ("Reliability", "neutral"))
    with metric_cols[3]: metric_card("Compact Retry", metadata.get("local_ai_compact_retry_used", "n/a"), ("Fallback", "neutral"))
    st.write(
        {
            "fresh_ingestion_status": metadata.get("fresh_openbb_ingestion_status"),
            "dedupe_enabled": metadata.get("fresh_openbb_ingestion_dedupe_enabled"),
            "local_ai_preflight_status": metadata.get("local_ai_preflight_status"),
            "local_ai_model_available": metadata.get("local_ai_model_available"),
            "local_ai_status": metadata.get("local_ai_status"),
        }
    )
    _show_json_field("Warnings", latest.get("warnings_json"))
    _show_json_field("Errors", latest.get("errors_json"))
    _show_json_field("Run metadata", latest.get("metadata_json"))

    if latest.get("local_ai_memo_id"):
        memo = fetch_dataframe(
            """
            SELECT memo_id, status, response_text, prompt_text, warnings_json
            FROM ai_research_memos
            WHERE memo_id = ?
            """,
            (latest["local_ai_memo_id"],),
        )
        section_header("Latest Local AI Memo")
        if memo.empty:
            st.info("Memo record not found.")
        else:
            row = memo.iloc[0]
            st.markdown(str(row["response_text"]) or "_No memo response text._")
            with st.expander("Stored prompt", expanded=False):
                st.code(str(row["prompt_text"]), language="markdown")

    section_header("Analytics Summary")
    analytics_path = latest.get("analytics_report_path")
    if analytics_path:
        csv_path = Path(str(analytics_path)).with_name("openbb_summary.csv")
        if csv_path.exists():
            dataframe_or_message(pd.read_csv(csv_path), "No analytics summary rows.")
        else:
            st.info(f"Analytics CSV not found beside report: {csv_path}")
