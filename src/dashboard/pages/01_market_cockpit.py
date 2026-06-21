from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.database import fetch_dataframe, initialize_database  # noqa: E402
from dashboard.components.charts import price_chart  # noqa: E402
from dashboard.components.signal_cards import render_signal  # noqa: E402
from dashboard.components.ui import (  # noqa: E402
    caveat_box,
    compact_dataframe,
    hero,
    metric_card,
    section_header,
    setup_page,
)


initialize_database()
setup_page()
hero(
    "Market Cockpit",
    "Local market context, trend features, and research decisions. Not financial advice; no orders are placed.",
    badges=[("Local data", "info"), ("Research action only", "success"), ("Plotly optional", "neutral")],
)
symbols = fetch_dataframe("SELECT DISTINCT symbol FROM market_data ORDER BY symbol")
symbol = st.selectbox("Symbol", symbols["symbol"].tolist() if not symbols.empty else ["BTC/USDT"])

market = fetch_dataframe(
    "SELECT * FROM market_data WHERE symbol = ? ORDER BY timestamp",
    (symbol,),
)
features = fetch_dataframe(
    """
    SELECT symbol, timeframe, timestamp,
           MAX(CASE WHEN feature_name='ema_20' THEN feature_value END) AS ema_20,
           MAX(CASE WHEN feature_name='ema_50' THEN feature_value END) AS ema_50,
           MAX(CASE WHEN feature_name='ema_200' THEN feature_value END) AS ema_200
    FROM features
    WHERE symbol = ?
    GROUP BY symbol, timeframe, timestamp
    ORDER BY timestamp
    """,
    (symbol,),
)
if not market.empty and not features.empty:
    market = market.merge(features[["timestamp", "ema_20", "ema_50", "ema_200"]], on="timestamp", how="left")

latest_close = "n/a"
coverage = "No local rows"
missing_close = 0
if not market.empty:
    latest_close = f"{float(market.iloc[-1]['close']):,.2f}" if market.iloc[-1].get("close") is not None else "n/a"
    coverage = f"{str(market.iloc[0]['timestamp'])[:10]} to {str(market.iloc[-1]['timestamp'])[:10]}"
    missing_close = int(market["close"].isna().sum())

cards = st.columns(4)
with cards[0]:
    metric_card("Selected Market", symbol, ("Local", "info"), "Current research view")
with cards[1]:
    metric_card("Latest Close", latest_close, ("Descriptive", "neutral"), "No execution meaning")
with cards[2]:
    metric_card("Data Coverage", coverage, (f"{len(market):,} rows", "success" if not market.empty else "warning"))
with cards[3]:
    metric_card("Missing Close", missing_close, ("Clean" if missing_close == 0 else "Review", "success" if missing_close == 0 else "warning"))

section_header("Price Context", "Native Streamlit fallback is used automatically when Plotly is unavailable")
price_chart(market.tail(250), f"{symbol} price and trend indicators")

regime = fetch_dataframe("SELECT * FROM regimes WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1", (symbol,))
decision = fetch_dataframe("SELECT * FROM decisions ORDER BY created_at DESC LIMIT 1")
left, right = st.columns(2)
with left:
    section_header("Current Regime", "Latest locally derived market regime")
    compact_dataframe(regime, height=180, empty_message="No regime record available.")
with right:
    section_header("Latest Research Decision", "Research output, not an instruction to trade")
    if decision.empty:
        st.info("No research decision recorded.")
    else:
        render_signal(decision.iloc[0].to_dict())

with st.expander("Raw market rows", expanded=False):
    compact_dataframe(market.tail(250), height=320, empty_message="No local market rows available.")
with st.expander("Raw feature rows", expanded=False):
    compact_dataframe(features.tail(250), height=320, empty_message="No local feature rows available.")

caveat_box("Research-only market review. Live execution, leverage, brokerage connections, and real orders are disabled.", "info")
