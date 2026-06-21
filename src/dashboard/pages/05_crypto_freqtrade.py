from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.database import fetch_dataframe, initialize_database  # noqa: E402
from dashboard.components.ui import caveat_box, compact_dataframe, hero, metric_card, setup_page  # noqa: E402


initialize_database()
setup_page()
hero(
    "Crypto Freqtrade",
    "Spot-only strategy research and backtest provenance. Dry-run configuration remains disabled by default.",
    badges=[("Spot research", "info"), ("No leverage", "success"), ("No orders", "success")],
)
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
with summary_cols[0]:
    metric_card("Generated Strategies", len(strategies), ("Research artifacts", "neutral"))
with summary_cols[1]:
    metric_card("Backtest Metrics", len(metrics), ("Simulation rows", "info"))
with summary_cols[2]:
    metric_card("Engine Runs", len(provenance), ("Provenance recorded", "success"))

with st.expander("Generated Strategies", expanded=True):
    compact_dataframe(strategies, height=320)
with st.expander("Pair-level Performance", expanded=False):
    compact_dataframe(metrics, height=320)
with st.expander("Engine Provenance", expanded=False):
    compact_dataframe(provenance, height=320)
caveat_box("internal_research_fallback is a demo research fallback, not a real Freqtrade CLI backtest or an execution path.", "warning")
