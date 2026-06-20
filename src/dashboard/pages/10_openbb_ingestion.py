from __future__ import annotations

import sys
from pathlib import Path

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
from data_brain.openbb_adapter import get_openbb_status  # noqa: E402


initialize_database()

st.title("OpenBB Ingestion")
st.caption("Research/data context only. No live trading, no broker configs, and no order placement.")

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

st.subheader("OpenBB Status")
status_cols = st.columns(4)
status_cols[0].metric("Installed", str(status["installed"]))
status_cols[1].metric("Status", str(status["status"]))
status_cols[2].metric("Safe For Live", str(status["safe_for_live"]))
status_cols[3].metric("Latest Run", str(latest_run.get("run_id", "none")))
st.dataframe([status], use_container_width=True, hide_index=True)

st.subheader("Latest Ingestion Runs")
dataframe_or_message(runs, "No OpenBB ingestion runs recorded yet. Use scripts/ingest_openbb_data.py.")

st.subheader("Market Data Summary")
dataframe_or_message(summary, "No OpenBB market data available.")

quality_left, quality_right = st.columns([1, 2])
with quality_left:
    st.subheader("Data Quality")
    st.metric("Duplicate Timestamps", quality["duplicate_timestamp_count"])
    st.metric("Missing Close", quality["missing_close_count"])
    st.metric("Non-Positive Prices", quality["non_positive_prices"])
    st.metric("High Below Low", quality["high_below_low_count"])
with quality_right:
    st.subheader("Provider / Source Counts")
    dataframe_or_message(quality["provider_source_summary"], "No provider/source counts available.")

st.subheader("Date Coverage")
dataframe_or_message(quality["date_coverage_by_symbol"], "No date coverage available.")

st.subheader("Normalized Close Index")
normalized = comparison["normalized_index"]
if normalized.empty:
    st.info("No normalized comparison available.")
else:
    chart = normalized.pivot_table(index="timestamp", columns="symbol", values="normalized_close", aggfunc="last")
    st.line_chart(chart)

st.subheader("Daily Return Correlation")
correlation = comparison["correlation_matrix"]
dataframe_or_message(correlation.reset_index().rename(columns={"index": "symbol"}), "Need at least two symbols for correlation.")

left, right = st.columns(2)
with left:
    st.subheader("Market Data Preview")
    market = fetch_dataframe(
        """
        SELECT symbol, asset_class, provider, interval, timestamp, open, high, low, close, volume, retrieved_at
        FROM openbb_market_data
        ORDER BY retrieved_at DESC, symbol, timestamp DESC
        LIMIT 100
        """
    )
    dataframe_or_message(market, "No OpenBB market data available.")

with right:
    st.subheader("Macro Data Preview")
    macro = fetch_dataframe(
        """
        SELECT indicator, provider, frequency, timestamp, value, retrieved_at
        FROM openbb_macro_data
        ORDER BY retrieved_at DESC, indicator, timestamp DESC
        LIMIT 100
        """
    )
    dataframe_or_message(macro, "No OpenBB macro data available.")

st.info(
    "Run ingestion from the CLI, for example: "
    "`python scripts/ingest_openbb_data.py --symbols AAPL MSFT NVDA --asset-class equity --start-date 2022-01-01`. "
    "This dashboard reads local database rows only."
)
