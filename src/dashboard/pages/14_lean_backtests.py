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
from lean_brain.lean_adapter import get_lean_status  # noqa: E402
from lean_brain.lean_runner import run_lean_backtest  # noqa: E402


def _show_json(label: str, value) -> None:
    with st.expander(label, expanded=False):
        try:
            st.json(json.loads(str(value or "{}")))
        except Exception:
            st.code(str(value))


initialize_database()

st.title("LEAN Backtests")
st.caption("Optional research-only local LEAN integration. No cloud login, brokerage credentials, live mode, or real orders.")

status = get_lean_status()
cols = st.columns(4)
cols[0].metric("LEAN CLI", "available" if status["lean_cli_available"] else "missing")
cols[1].metric("Docker", "available" if status["docker_available"] else "missing")
cols[2].metric("Mode", status["mode"])
cols[3].metric("Safe for live", str(status["safe_for_live"]))
if status["warnings"]:
    st.warning("; ".join(status["warnings"]))
if status["errors"]:
    st.error("; ".join(status["errors"]))

with st.form("lean_research_form"):
    symbols_text = st.text_input("Symbols", value="AAPL MSFT")
    provider = st.text_input("Provider", value="yfinance")
    interval = st.text_input("Interval", value="1d")
    strategy_name = st.text_input("Strategy name", value="equal_weight_demo")
    cash = st.number_input("Research cash", value=100000.0, min_value=1.0)
    create_skeleton = st.form_submit_button("Create research-only LEAN skeleton")
    run_local = False
    if status["lean_cli_available"]:
        run_local = st.form_submit_button("Run local LEAN backtest")

if create_skeleton or run_local:
    result = run_lean_backtest(
        symbols=[part.strip() for part in symbols_text.split() if part.strip()],
        provider=provider.strip() or "yfinance",
        interval=interval.strip() or "1d",
        strategy_name=strategy_name.strip() or "equal_weight_demo",
        cash=float(cash),
        skip_run=not run_local,
    )
    st.success(f"LEAN research run saved: {result['run_id']} ({result['status']})")
    if result["warnings"]:
        st.warning("; ".join(result["warnings"]))
    if result["errors"]:
        st.error("; ".join(result["errors"]))

runs = fetch_dataframe(
    """
    SELECT run_id, created_at, finished_at, status, symbols, strategy_name,
           project_path, report_path, metrics_json, warnings_json, errors_json, engine_status
    FROM lean_backtest_runs
    ORDER BY created_at DESC
    LIMIT 25
    """
)
st.subheader("Latest LEAN Research Runs")
dataframe_or_message(runs, "No LEAN research runs recorded yet.")

if not runs.empty:
    latest = runs.iloc[0]
    st.subheader("Latest Run Details")
    st.write(
        {
            "run_id": latest["run_id"],
            "status": latest["status"],
            "project_path": latest["project_path"],
            "report_path": latest["report_path"],
        }
    )
    _show_json("Engine status", latest["engine_status"])
    _show_json("Metrics", latest["metrics_json"])
    _show_json("Warnings", latest["warnings_json"])
    _show_json("Errors", latest["errors_json"])
    metrics = fetch_dataframe(
        """
        SELECT run_id, symbol, metric_name, metric_value, metric_text, created_at
        FROM lean_backtest_metrics
        WHERE run_id = ?
        ORDER BY metric_name
        """,
        (latest["run_id"],),
    )
    st.subheader("Parsed Metrics")
    dataframe_or_message(metrics, "No parsed LEAN metrics available.")
