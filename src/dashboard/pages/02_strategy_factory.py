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
    "Strategy Factory",
    "Inspect generated research specifications and conversion artifacts before any backtest review.",
    badges=[("Research specifications", "info"), ("No execution", "success")],
)
specs = fetch_dataframe("SELECT * FROM strategy_specs ORDER BY created_at DESC")
if specs.empty:
    st.info("No YAML strategy specs generated yet.")
else:
    valid_count = int((specs["validation_status"].astype(str).str.lower() == "valid").sum()) if "validation_status" in specs else 0
    selected = st.selectbox("Strategy", specs["strategy_name"].tolist())
    row = specs[specs["strategy_name"] == selected].iloc[0]
    cards = st.columns(3)
    with cards[0]:
        metric_card("Specifications", len(specs), ("Local records", "neutral"))
    with cards[1]:
        metric_card("Validated", valid_count, ("Schema checks", "success" if valid_count else "warning"))
    with cards[2]:
        metric_card("Selected Status", row["validation_status"], (selected, "info"))
    section_header("Research Rationale")
    caveat_box(str(row["rationale"]), "info")
    with st.expander("Strategy YAML", expanded=False):
        st.code(row["source_yaml"], language="yaml")
    generated = fetch_dataframe("SELECT * FROM generated_strategies WHERE strategy_id = ?", (selected,))
    with st.expander("Convert-to-engine artifacts", expanded=False):
        compact_dataframe(generated, height=280, empty_message="No generated engine artifact for this strategy.")

caveat_box("Specifications are research inputs. They do not authorize live trading or order placement.", "neutral")
