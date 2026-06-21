from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lean_brain.lean_backtest_runner import get_lean_status  # noqa: E402
from qlib_brain.qlib_experiment_runner import get_qlib_status, run_basic_experiment  # noqa: E402
from dashboard.components.ui import caveat_box, compact_dataframe, hero, setup_page  # noqa: E402


setup_page()
hero(
    "Equity LEAN + Qlib",
    "A compact lab view for optional local equity research engines and their current limitations.",
    badges=[("Research lab", "info"), ("Execution unverified", "warning")],
)
with st.expander("Engine status details", expanded=False):
    compact_dataframe(pd.DataFrame([get_lean_status(), get_qlib_status()]), height=200)
with st.expander("Baseline experiment notes", expanded=False):
    st.write(run_basic_experiment())
caveat_box("LEAN executable backtesting remains unverified, and the Qlib trainer package is not installed. This page does not execute orders.", "warning")
