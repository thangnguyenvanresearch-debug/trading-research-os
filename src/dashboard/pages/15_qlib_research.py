from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.database import fetch_dataframe, initialize_database  # noqa: E402
from dashboard.components.tables import dataframe_or_message  # noqa: E402
from qlib_brain.qlib_adapter import get_qlib_status  # noqa: E402
from qlib_brain.qlib_runner import run_qlib_experiment  # noqa: E402


def _show_json(label: str, value) -> None:
    with st.expander(label, expanded=False):
        try:
            st.json(json.loads(str(value or "{}")))
        except Exception:
            st.code(str(value))


initialize_database()

st.title("Qlib Research")
st.caption("Research-only ML/factor analysis. Not trading advice. This page does not place orders.")

status = get_qlib_status()
cols = st.columns(4)
cols[0].metric("Qlib package", "available" if status["qlib_import_available"] else "missing")
cols[1].metric("Status", status["status"])
cols[2].metric("Mode", status["mode"])
cols[3].metric("Live execution allowed", str(status["safe_for_live"]))
if status["version"]:
    st.write({"version": status["version"]})
if status["warnings"]:
    st.warning("; ".join(status["warnings"]))
if status["errors"]:
    st.error("; ".join(status["errors"]))
if not status["qlib_import_available"]:
    st.info("Dataset export remains available. The true Qlib trainer is not installed and experiment execution is unavailable.")

with st.form("qlib_research_form"):
    symbols_text = st.text_input("Symbols", value="AAPL MSFT")
    provider = st.text_input("Provider", value="yfinance")
    interval = st.text_input("Interval", value="1d")
    experiment_name = st.text_input("Experiment name", value="qlib_demo")
    horizon_days = st.number_input("Label horizon days", value=5, min_value=1, max_value=60)
    export_only = st.form_submit_button("Export Qlib research dataset")
    run_experiment = st.form_submit_button("Run Qlib research experiment")

if export_only or run_experiment:
    result = run_qlib_experiment(
        symbols=[part.strip() for part in symbols_text.split() if part.strip()],
        provider=provider.strip() or "yfinance",
        interval=interval.strip() or "1d",
        experiment_name=experiment_name.strip() or "qlib_demo",
        horizon_days=int(horizon_days),
        skip_run=export_only,
    )
    st.success(f"Qlib research run saved: {result['run_id']} ({result['status']})")
    if result["warnings"]:
        st.warning("; ".join(result["warnings"]))
    if result["errors"]:
        st.error("; ".join(result["errors"]))

exports = fetch_dataframe(
    """
    SELECT export_id, created_at, status, symbols, provider, interval,
           feature_count, row_count, output_path, manifest_path, warnings_json, errors_json
    FROM qlib_dataset_exports
    ORDER BY created_at DESC
    LIMIT 25
    """
)
st.subheader("Latest Dataset Exports")
export_cols = st.columns(2)
export_cols[0].metric("Dataset exports", len(exports))
export_cols[1].metric("Latest rows", int(exports.iloc[0]["row_count"]) if not exports.empty else 0)
with st.expander("Dataset export history", expanded=False):
    dataframe_or_message(exports, "No Qlib dataset exports recorded yet.", height=320)

runs = fetch_dataframe(
    """
    SELECT run_id, created_at, finished_at, status, symbols, experiment_name,
           qlib_available, dataset_export_id, report_path, metrics_json, warnings_json, errors_json
    FROM qlib_experiment_runs
    ORDER BY created_at DESC
    LIMIT 25
    """
)
st.subheader("Latest Qlib Research Runs")
run_cols = st.columns(2)
run_cols[0].metric("Recorded runs", len(runs))
run_cols[1].metric("Latest status", str(runs.iloc[0]["status"]) if not runs.empty else "none")
with st.expander("Qlib run history", expanded=False):
    dataframe_or_message(runs, "No Qlib research runs recorded yet.", height=320)

if not runs.empty:
    latest = runs.iloc[0]
    st.subheader("Latest Run Details")
    st.write(
        {
            "run_id": latest["run_id"],
            "status": latest["status"],
            "dataset_export_id": latest["dataset_export_id"],
            "report_path": latest["report_path"],
        }
    )
    _show_json("Metrics", latest["metrics_json"])
    _show_json("Warnings", latest["warnings_json"])
    _show_json("Errors", latest["errors_json"])
    predictions = fetch_dataframe(
        """
        SELECT run_id, symbol, timestamp, score, label, model_name, created_at
        FROM qlib_predictions
        WHERE run_id = ?
        ORDER BY symbol, timestamp DESC
        LIMIT 100
        """,
        (latest["run_id"],),
    )
    with st.expander("Predictions / Scores", expanded=False):
        dataframe_or_message(predictions, "No real Qlib predictions recorded for this run.", height=320)
