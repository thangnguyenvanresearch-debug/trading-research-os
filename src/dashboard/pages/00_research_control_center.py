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
from dashboard.components.ui import (  # noqa: E402
    caveat_box,
    compact_dataframe,
    hero,
    metric_card,
    section_header,
    setup_page,
)
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
setup_page()

hero(
    "Research Control Center",
    "Private local-first market research OS. Research-only. No live trading. No orders.",
    badges=[
        ("Research only", "success"),
        ("No orders", "success"),
        ("No broker credentials", "neutral"),
        ("Local-first", "info"),
        ("Private repo", "neutral"),
    ],
)

statuses = get_latest_engine_statuses()
checklist = build_safety_checklist()
unsafe_count = int((checklist["status"] == "unsafe").sum()) if not checklist.empty else 0
health = get_openbb_data_health()

row_one = st.columns(3)
with row_one[0]:
    metric_card("Data", f"{statuses['openbb']['rows']:,} rows", (statuses["openbb"]["status"], "success"), "Local OpenBB market data")
with row_one[1]:
    ai_available = statuses["local_ai"]["status"] == "available"
    metric_card("Local AI", statuses["local_ai"]["status"], (statuses["local_ai"]["status"], "success" if ai_available else "warning"), f"Model: {statuses['local_ai'].get('model')}")
with row_one[2]:
    metric_card("Daily Research", statuses["latest_daily_run"]["status"], ("Latest DB run", "info"), "Scheduler state is not verified here")

row_two = st.columns(3)
with row_two[0]:
    lean_verified = bool(statuses["lean"].get("executable_verified"))
    metric_card("LEAN", "Executable verified" if lean_verified else "Executable unverified", ("CLI / skeleton available", "warning" if not lean_verified else "success"), str(statuses["lean"].get("latest_executable_status")))
with row_two[1]:
    qlib_available = bool(statuses["qlib"].get("available"))
    metric_card("Qlib", "Trainer available" if qlib_available else "Dataset export only", ("Package missing" if not qlib_available else "Available", "warning" if not qlib_available else "success"), "True Qlib execution is optional")
with row_two[2]:
    metric_card("Safety", f"{unsafe_count} unsafe", ("Controls disabled", "success" if unsafe_count == 0 else "danger"), "Live and order paths remain off")

section_header("What this means", "A quick reading guide for the current workstation state")
meaning_cols = st.columns(3)
with meaning_cols[0]:
    caveat_box("Healthy: OpenBB rows are local data availability, and the safety count confirms disabled execution controls.", "success")
with meaning_cols[1]:
    caveat_box("Caveat: Daily Research is the latest database run, not proof that Windows Task Scheduler is currently active.", "warning")
with meaning_cols[2]:
    caveat_box("Future work: LEAN execution remains unverified; Qlib dataset export works while its trainer package is missing.", "neutral")

qlib_exports = get_latest_qlib_exports(1)
lean_runs = get_latest_lean_runs(1)

section_header("Next Actions", "Static recommendations based on local status only")
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
    dataframe_or_message(checklist, "Safety checklist unavailable.")
    if not checklist.empty and (checklist["status"] == "unsafe").any():
        st.error("One or more safety checks are unsafe. Do not run research workflows until fixed.")

with st.expander("Raw Debug Tables", expanded=False):
    st.write("OpenBB rows by symbol")
    compact_dataframe(health["rows_by_symbol"], height=240, empty_message="No OpenBB market rows found.")
    st.write("Duplicate timestamp groups")
    compact_dataframe(health["duplicates"], height=220, empty_message="No duplicate timestamp groups detected.")
    st.write("Raw status JSON")
    st.code(json.dumps(statuses, indent=2, default=str), language="json")
