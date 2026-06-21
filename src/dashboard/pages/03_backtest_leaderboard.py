from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.database import fetch_dataframe, initialize_database  # noqa: E402


initialize_database()
st.title("Backtest Leaderboard")
st.caption("Research comparison only. Backtests are not proof of future performance.")
df = fetch_dataframe(
    """
    SELECT bm.strategy_id, bm.total_return, bm.out_of_sample_return, bm.max_drawdown,
           bm.sharpe, bm.sortino, bm.win_rate, bm.trade_count, bm.profit_factor,
           bm.fee_slippage_adjusted_return, rr.status, rr.flags
    FROM backtest_metrics bm
    LEFT JOIN risk_reviews rr ON rr.run_id = bm.run_id
    ORDER BY bm.fee_slippage_adjusted_return DESC
    """
)
summary_cols = st.columns(3)
summary_cols[0].metric("Strategies reviewed", len(df))
summary_cols[1].metric("Top strategy", str(df.iloc[0]["strategy_id"]) if not df.empty else "none")
summary_cols[2].metric(
    "Top adjusted return",
    f"{float(df.iloc[0]['fee_slippage_adjusted_return']):.2%}" if not df.empty else "n/a",
)

with st.expander("Full leaderboard", expanded=True):
    if df.empty:
        st.info("No backtest metrics recorded yet.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True, height=360)
