from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

SRC = Path(__file__).resolve().parents[1]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.database import fetch_dataframe, initialize_database  # noqa: E402
from core.config_loader import load_global_config  # noqa: E402
from core.validation import assert_research_only  # noqa: E402
from dashboard.components.signal_cards import render_signal  # noqa: E402
from dashboard.components.tables import dataframe_or_message  # noqa: E402
from data_brain.openbb_adapter import get_openbb_status  # noqa: E402
from freqtrade_brain.batch_backtest_runner import freqtrade_cli_available  # noqa: E402
from hummingbot_brain.spread_scanner import get_hummingbot_status  # noqa: E402
from lean_brain.lean_backtest_runner import get_lean_status  # noqa: E402
from nautilus_brain.nautilus_adapter import get_nautilus_status  # noqa: E402
from qlib_brain.qlib_experiment_runner import get_qlib_status  # noqa: E402


st.set_page_config(page_title="Trading Research OS", layout="wide")
assert_research_only(load_global_config())
initialize_database()

st.title("Multi-Brain AI Trading Research OS")
st.caption("Research, backtesting, paper trading, and strategy validation. Live trading is disabled in v1.")

left, right = st.columns([2, 1])
with left:
    st.subheader("Decision Cockpit")
    decisions = fetch_dataframe("SELECT * FROM decisions ORDER BY created_at DESC LIMIT 10")
    dataframe_or_message(decisions, "No decisions yet. Run the v1 pipeline through score_strategies.py.")
with right:
    st.subheader("Latest Signal")
    if decisions.empty:
        st.info("No signal available.")
    else:
        render_signal(decisions.iloc[0].to_dict())

st.subheader("Backtest Leaderboard")
leaderboard = fetch_dataframe(
    """
    SELECT bm.strategy_id, bm.total_return, bm.out_of_sample_return, bm.max_drawdown,
           bm.sharpe, bm.sortino, bm.win_rate, bm.trade_count, bm.profit_factor,
           bm.fee_slippage_adjusted_return, rr.status, rr.flags
    FROM backtest_metrics bm
    LEFT JOIN risk_reviews rr ON rr.run_id = bm.run_id
    ORDER BY bm.fee_slippage_adjusted_return DESC
    """
)
dataframe_or_message(leaderboard, "No backtest metrics yet.")

diag_left, diag_right = st.columns(2)
with diag_left:
    st.subheader("Data Sources")
    sources = fetch_dataframe(
        "SELECT source, COUNT(*) AS candles FROM market_data GROUP BY source ORDER BY candles DESC"
    )
    dataframe_or_message(sources, "No market data sources recorded yet.")
with diag_right:
    st.subheader("Engine Status")
    statuses = [
        {
            "engine": "freqtrade",
            "installed": freqtrade_cli_available(),
            "status": "partial",
            "role": "v1 crypto backtest/fallback path",
            "current_capability": "Generated strategy conversion, internal fallback, and CLI export parsing when installed.",
            "next_step": "Use --use-freqtrade-cli only after installing Freqtrade and downloading data.",
            "safe_for_live": False,
        },
        get_openbb_status(),
        get_lean_status(),
        get_qlib_status(),
        get_hummingbot_status(),
        get_nautilus_status(),
    ]
    st.dataframe(
        statuses,
        use_container_width=True,
        hide_index=True,
    )

st.subheader("Backtest Engine Provenance")
engine_runs = fetch_dataframe(
    """
    SELECT br.strategy_id, br.engine, br.status, bm.parser_warnings
    FROM backtest_runs br
    LEFT JOIN backtest_metrics bm ON bm.run_id = br.run_id
    ORDER BY br.completed_at DESC
    LIMIT 20
    """
)
dataframe_or_message(engine_runs, "No backtest run provenance yet.")

st.subheader("Safety Defaults")
st.write("- Real-money live trading: `disabled`")
st.write("- Futures: `disabled`")
st.write("- Leverage: `disabled`")
st.write("- Highest v1 permission: `APPROVED_FOR_DRY_RUN`")
