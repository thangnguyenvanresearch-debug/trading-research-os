from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.database import fetch_dataframe, initialize_database  # noqa: E402
from dashboard.components.ui import caveat_box, compact_dataframe, hero, metric_card, section_header, setup_page  # noqa: E402


initialize_database()
setup_page()
hero(
    "Backtest Leaderboard",
    "Compare simulation evidence and risk-gate outcomes. Backtests are not proof of future performance.",
    badges=[("Research comparison", "info"), ("No capital allocation", "success")],
)
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
rejected_count = int(df["status"].astype(str).str.lower().eq("rejected").sum()) if not df.empty else 0
low_trade_count = int((df["trade_count"].fillna(0) < 20).sum()) if not df.empty else 0
best_return = f"{float(df.iloc[0]['fee_slippage_adjusted_return']):.2%}" if not df.empty else "n/a"
summary_cols = st.columns(4)
with summary_cols[0]:
    metric_card("Strategies", len(df), ("Reviewed", "neutral"))
with summary_cols[1]:
    metric_card("Rejected", rejected_count, ("Risk gate", "warning" if rejected_count else "success"))
with summary_cols[2]:
    metric_card("Best Research Result", best_return, ("Adjusted return", "info"), "Simulation only")
with summary_cols[3]:
    metric_card("Low Trade Count", low_trade_count, ("Under 20 trades", "warning" if low_trade_count else "success"))

section_header("Research Ranking", "Full evidence remains available without dominating the first screen")
with st.expander("Open full leaderboard", expanded=False):
    compact_dataframe(df, height=360, empty_message="No backtest metrics recorded yet.")
caveat_box("High simulated returns can be fragile. Review drawdown, trade count, fees, and out-of-sample behavior before advancing a candidate.", "warning")
