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
from dashboard.components.ui import caveat_box, compact_dataframe, hero, metric_card, section_header, setup_page  # noqa: E402
from lean_brain.lean_adapter import get_lean_status  # noqa: E402
from lean_brain.lean_runner import run_lean_backtest  # noqa: E402


def _show_json(label: str, value) -> None:
    with st.expander(label, expanded=False):
        try:
            st.json(json.loads(str(value or "{}")))
        except Exception:
            st.code(str(value))


initialize_database()
setup_page()
hero(
    "LEAN Backtests",
    "Build local research data and project skeletons for the optional LEAN CLI.",
    badges=[("Research only", "success"), ("CLI optional", "neutral"), ("Executable unverified", "warning")],
)

status = get_lean_status()
cols = st.columns(4)
with cols[0]: metric_card("LEAN CLI", "Available" if status["lean_cli_available"] else "Missing", ("Detected locally", "success" if status["lean_cli_available"] else "warning"))
with cols[1]: metric_card("Docker", "Available" if status["docker_available"] else "Missing", ("Runtime", "neutral"))
with cols[2]: metric_card("Mode", status["mode"], ("Research only", "info"))
with cols[3]: metric_card("Live Execution", "Disabled", ("safe_for_live=False", "success"))
if status["warnings"]:
    st.warning("; ".join(status["warnings"]))
if status["errors"]:
    st.error("; ".join(status["errors"]))
caveat_box("LEAN data bridge and skeleton are available. Executable local backtesting remains unverified after a Docker/runtime timeout.", "warning")

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
section_header("Latest LEAN Research Runs")
run_cols = st.columns(2)
with run_cols[0]: metric_card("Recorded Runs", len(runs), ("Local history", "neutral"))
with run_cols[1]: metric_card("Latest Status", str(runs.iloc[0]["status"]) if not runs.empty else "none", ("Not proof of execution", "warning"))
with st.expander("LEAN run history", expanded=False):
    dataframe_or_message(runs, "No LEAN research runs recorded yet.", height=320)

if not runs.empty:
    latest = runs.iloc[0]
    section_header("Latest Run Details")
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
    with st.expander("Parsed Metrics", expanded=False):
        dataframe_or_message(metrics, "No parsed LEAN metrics available.", height=280)
