from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hummingbot_brain.inventory_risk_simulator import inventory_risk  # noqa: E402
from hummingbot_brain.market_making_lab import quote_distance_simulation  # noqa: E402
from hummingbot_brain.spread_scanner import get_hummingbot_status  # noqa: E402


st.title("Market Making Lab")
st.caption("Paper-only spread and inventory experiments. No live market making.")
st.dataframe([get_hummingbot_status()], use_container_width=True, hide_index=True)
mid = st.number_input("Mid price", value=65000.0)
spread = st.number_input("Quote distance bps", value=10.0)
st.write(quote_distance_simulation(mid, spread))
st.write(inventory_risk(base_position=0.45, target_position=0.50, max_deviation=0.10))
