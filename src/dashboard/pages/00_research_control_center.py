from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.database import initialize_database  # noqa: E402
from dashboard.components.tables import dataframe_or_message  # noqa: E402
from dashboard.control_center import (  # noqa: E402
    build_latest_runs,
    build_next_actions,
    build_safety_checklist,
    get_latest_engine_statuses,
    get_latest_lean_runs,
    get_latest_qlib_exports,
    get_openbb_data_health,
    load_engine_registry,
)


initialize_database()

st.title("Research Control Center")
st.caption("Unified read-only status for local research engines. No credentials, live trading, or orders.")

statuses = get_latest_engine_statuses()
cols = st.columns(6)
cols[0].metric("OpenBB rows", str(statuses["openbb"]["rows"]), statuses["openbb"]["status"])
cols[1].metric("Local AI", statuses["local_ai"]["status"], str(statuses["local_ai"].get("model")))
cols[2].metric(
    "Latest Daily Run",
    statuses["latest_daily_run"]["status"],
    f"scheduler={statuses['latest_daily_run']['scheduler_state']}",
)
cols[3].metric(
    "LEAN",
    str(statuses["lean"]["status"]),
    f"cli={statuses['lean']['cli_detected']} exec={statuses['lean']['latest_executable_status']}",
)
cols[4].metric("Qlib", str(statuses["qlib"]["status"]), f"installed={statuses['qlib']['available']}")
cols[5].metric("Safety", statuses["safety"]["status"])

if not statuses["lean"].get("executable_verified"):
    st.warning("LEAN CLI/skeleton may be available, but executable LEAN backtest remains unverified until a local Docker/runtime run completes.")
st.info("Daily status is the latest pipeline DB run. Windows Task Scheduler state is not queried by this page.")

st.subheader("What this means")
meaning_left, meaning_right = st.columns(2)
with meaning_left:
    st.markdown(
        """
        - **OpenBB rows** measure local data availability, not market freshness guarantees.
        - **Local AI** reflects whether the local Ollama runtime answers now.
        - **Daily run** is the latest database record, not proof that Windows Task Scheduler is active.
        """
    )
with meaning_right:
    st.markdown(
        """
        - **LEAN** has a data bridge and skeleton; executable backtesting remains unverified.
        - **Qlib** dataset export works; the Qlib trainer package is not installed.
        - **Safety** means live execution and real-order controls remain disabled.
        """
    )

st.subheader("Data Health")
health = get_openbb_data_health()
st.metric("Local OpenBB rows", health["total_rows"])
dataframe_or_message(health["rows_by_symbol"], "No OpenBB market rows found.")
with st.expander("Duplicate timestamp check", expanded=False):
    dataframe_or_message(health["duplicates"], "No OpenBB duplicate timestamp groups detected.")

qlib_exports = get_latest_qlib_exports(1)
lean_runs = get_latest_lean_runs(1)

st.subheader("Next Actions")
for action in build_next_actions():
    st.write(f"- {action}")

with st.expander("Engine Registry", expanded=False):
    dataframe_or_message(load_engine_registry(), "Engine registry unavailable.")

with st.expander("Latest Runs And Artifacts", expanded=False):
    latest_runs = build_latest_runs(limit=5)
    dataframe_or_message(latest_runs, "No research runs recorded yet.")
    st.write("Latest Qlib dataset")
    dataframe_or_message(qlib_exports, "No Qlib dataset export recorded.")
    st.write("Latest LEAN research artifact")
    dataframe_or_message(lean_runs, "No LEAN run recorded.")

with st.expander("Safety Details", expanded=False):
    checklist = build_safety_checklist()
    dataframe_or_message(checklist, "Safety checklist unavailable.")
    if not checklist.empty and (checklist["status"] == "unsafe").any():
        st.error("One or more safety checks are unsafe. Do not run research workflows until fixed.")

with st.expander("Raw Status JSON", expanded=False):
    st.code(json.dumps(statuses, indent=2, default=str), language="json")
