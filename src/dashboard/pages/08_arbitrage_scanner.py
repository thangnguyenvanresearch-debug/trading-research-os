from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hummingbot_brain.arbitrage_alert_engine import opportunity_score  # noqa: E402
from hummingbot_brain.spread_scanner import scan_spread  # noqa: E402
from dashboard.components.ui import caveat_box, hero, setup_page  # noqa: E402


setup_page()
hero("Arbitrage Scanner", "A local alert-only spread calculator with no execution path.", badges=[("Alert only", "info"), ("No auto-execution", "success")])
bid = st.number_input("Best bid", value=64990.0)
ask = st.number_input("Best ask", value=65020.0)
spread = scan_spread("BTC/USDT", bid, ask)
alert = opportunity_score(spread["gross_spread"], fees=0.002, slippage=0.0005)
st.write({**spread, **alert})
caveat_box("A positive spread score is a research observation, not a buy/sell instruction.", "warning")
