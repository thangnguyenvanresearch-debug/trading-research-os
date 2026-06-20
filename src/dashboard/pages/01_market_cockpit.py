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


initialize_database()
st.title("Market Cockpit")
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
price_chart(market.tail(250), f"{symbol} price and trend indicators")

regime = fetch_dataframe("SELECT * FROM regimes WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1", (symbol,))
decision = fetch_dataframe("SELECT * FROM decisions ORDER BY created_at DESC LIMIT 1")
left, right = st.columns(2)
with left:
    st.subheader("Current Regime")
    st.dataframe(regime, use_container_width=True, hide_index=True)
with right:
    st.subheader("Latest Decision")
    if decision.empty:
        st.info("No decision recorded.")
    else:
        render_signal(decision.iloc[0].to_dict())

