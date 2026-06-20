from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lean_brain.lean_backtest_runner import get_lean_status  # noqa: E402
from qlib_brain.qlib_experiment_runner import get_qlib_status, run_basic_experiment  # noqa: E402


st.title("Equity LEAN + Qlib")
st.dataframe([get_lean_status(), get_qlib_status()], use_container_width=True, hide_index=True)
st.write(run_basic_experiment())
st.info("Phase 3 will add factor research, ML signals, portfolio backtests, and benchmark comparison.")
