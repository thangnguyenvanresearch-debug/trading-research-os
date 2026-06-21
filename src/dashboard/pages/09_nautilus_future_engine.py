from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nautilus_brain.nautilus_adapter import get_nautilus_status, nautilus_status  # noqa: E402
from nautilus_brain.nautilus_strategy_skeleton import skeleton_notes  # noqa: E402
from dashboard.components.ui import caveat_box, compact_dataframe, hero, setup_page  # noqa: E402
import pandas as pd


setup_page()
hero("Nautilus Future Engine", "A future research-engine placeholder. It is not connected to live execution.", badges=[("Future work", "neutral"), ("Research only", "success")])
with st.expander("Adapter status", expanded=False):
    compact_dataframe(pd.DataFrame([get_nautilus_status()]), height=180)
st.write(nautilus_status())
st.write(skeleton_notes())
caveat_box("Future work may add shared simulation models. Live trading, futures, leverage, and order execution remain out of scope.", "neutral")
