from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analytics.openbb_analytics import (  # noqa: E402
    compute_openbb_data_quality,
    compute_openbb_pair_comparison,
    compute_openbb_return_summary,
    load_openbb_prices,
)
from core.database import fetch_dataframe, initialize_database  # noqa: E402
from dashboard.components.tables import dataframe_or_message  # noqa: E402
from dashboard.components.ui import caveat_box, compact_dataframe, hero, metric_card, section_header, setup_page  # noqa: E402
from data_brain.openbb_adapter import get_openbb_status  # noqa: E402


initialize_database()
setup_page()

hero(
    "OpenBB Local Data",
    "Read-only analytics over locally ingested market data. Dashboard load never fetches provider data.",
    badges=[("Local database", "info"), ("Read-only page", "success"), ("No credentials", "neutral")],
)

status = get_openbb_status()
runs = fetch_dataframe(
    """
    SELECT run_id, started_at, finished_at, status, rows_inserted, rows_failed,
           provider_summary_json, warnings_json, errors_json
    FROM openbb_ingestion_runs
    ORDER BY started_at DESC
    LIMIT 20
    """
)
latest_run = runs.iloc[0].to_dict() if not runs.empty else {}
prices = load_openbb_prices()
summary = compute_openbb_return_summary(prices)
quality = compute_openbb_data_quality(prices)
comparison = compute_openbb_pair_comparison(prices)

status_cols = st.columns(4)
with status_cols[0]:
    metric_card("OpenBB Package", "Installed" if status["installed"] else "Missing", (status["status"], "success" if status["installed"] else "warning"))
with status_cols[1]:
    metric_card("Local Rows", len(prices), ("Database", "info"))
with status_cols[2]:
    metric_card("Latest Run", latest_run.get("status", "none"), (latest_run.get("run_id", "No run"), "neutral"))
with status_cols[3]:
    metric_card("Live Execution", "Disabled", ("Research only", "success"))

section_header("Market Overview", "Descriptive return, drawdown, volatility, and coverage statistics")
compact_dataframe(summary, height=260, empty_message="No OpenBB market data available.")

quality_left, quality_right = st.columns([1, 2])
with quality_left:
    section_header("Data Quality")
    quality_cards = st.columns(2)
    with quality_cards[0]:
        metric_card("Duplicates", quality["duplicate_timestamp_count"], ("Clean" if quality["duplicate_timestamp_count"] == 0 else "Review", "success" if quality["duplicate_timestamp_count"] == 0 else "warning"))
        metric_card("Missing Close", quality["missing_close_count"], ("Quality", "neutral"))
    with quality_cards[1]:
        metric_card("Non-Positive", quality["non_positive_prices"], ("Quality", "neutral"))
        metric_card("High Below Low", quality["high_below_low_count"], ("Quality", "neutral"))
with quality_right:
    section_header("Normalized Close Index", "Base 100 comparison from local data")
    normalized = comparison["normalized_index"]
    if normalized.empty:
        st.info("No normalized comparison available.")
    else:
        chart = normalized.pivot_table(index="timestamp", columns="symbol", values="normalized_close", aggfunc="last")
        st.line_chart(chart)

section_header("Daily Return Correlation")
correlation = comparison["correlation_matrix"]
dataframe_or_message(correlation.reset_index().rename(columns={"index": "symbol"}), "Need at least two symbols for correlation.")

market = fetch_dataframe(
        """
        SELECT symbol, asset_class, provider, interval, timestamp, open, high, low, close, volume, retrieved_at
        FROM openbb_market_data
        ORDER BY retrieved_at DESC, symbol, timestamp DESC
        LIMIT 100
        """
    )
macro = fetch_dataframe(
        """
        SELECT indicator, provider, frequency, timestamp, value, retrieved_at
        FROM openbb_macro_data
        ORDER BY retrieved_at DESC, indicator, timestamp DESC
        LIMIT 100
        """
    )
with st.expander("Ingestion runs and local data details", expanded=False):
    st.write("Latest ingestion runs")
    compact_dataframe(runs, height=280, empty_message="No OpenBB ingestion runs recorded yet.")
    st.write("Provider / source counts")
    compact_dataframe(quality["provider_source_summary"], height=220, empty_message="No provider/source counts available.")
    st.write("Date coverage")
    compact_dataframe(quality["date_coverage_by_symbol"], height=220, empty_message="No date coverage available.")
    st.write("Adapter status")
    compact_dataframe(pd.DataFrame([status]), height=180)

with st.expander("Market and macro previews", expanded=False):
    st.write("Market data preview")
    compact_dataframe(market, height=280, empty_message="No OpenBB market data available.")
    st.write("Macro data preview")
    compact_dataframe(macro, height=240, empty_message="No OpenBB macro data available.")

caveat_box(
    "Run ingestion from the CLI, for example: "
    "`python scripts/ingest_openbb_data.py --symbols AAPL MSFT NVDA --asset-class equity --start-date 2022-01-01`. "
    "This dashboard reads local database rows only.",
    "info",
)
