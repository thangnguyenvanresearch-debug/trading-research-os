from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nautilus_brain.nautilus_adapter import get_nautilus_status, nautilus_status  # noqa: E402
from nautilus_brain.nautilus_strategy_skeleton import skeleton_notes  # noqa: E402


st.title("Nautilus Future Engine")
st.dataframe([get_nautilus_status()], use_container_width=True, hide_index=True)
st.write(nautilus_status())
st.write(skeleton_notes())
st.info("Phase 5 target: shared event model, simulation/live consistency, and migration from Freqtrade/LEAN research outputs.")
