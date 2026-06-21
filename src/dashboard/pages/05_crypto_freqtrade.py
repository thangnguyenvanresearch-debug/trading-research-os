from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.database import fetch_dataframe, initialize_database  # noqa: E402


initialize_database()
st.title("Crypto Freqtrade")
st.caption("Spot-only research strategies. Dry-run config generation is available but disabled by default.")
strategies = fetch_dataframe("SELECT * FROM generated_strategies WHERE engine_target='freqtrade'")
metrics = fetch_dataframe("SELECT * FROM backtest_metrics")
provenance = fetch_dataframe(
    """
    SELECT br.run_id, br.strategy_id, br.engine, br.status, br.notes, bm.parser_warnings
    FROM backtest_runs br
    LEFT JOIN backtest_metrics bm ON bm.run_id = br.run_id
    ORDER BY br.completed_at DESC
    """
)

summary_cols = st.columns(3)
summary_cols[0].metric("Generated strategies", len(strategies))
summary_cols[1].metric("Backtest metric rows", len(metrics))
summary_cols[2].metric("Recorded engine runs", len(provenance))

with st.expander("Generated Strategies", expanded=True):
    st.dataframe(strategies, use_container_width=True, hide_index=True, height=320)
with st.expander("Pair-level Performance", expanded=False):
    st.dataframe(metrics, use_container_width=True, hide_index=True, height=320)
with st.expander("Engine Provenance", expanded=False):
    st.dataframe(provenance, use_container_width=True, hide_index=True, height=320)
st.info("`internal_research_fallback` is a demo/research fallback, not a real Freqtrade CLI backtest.")
