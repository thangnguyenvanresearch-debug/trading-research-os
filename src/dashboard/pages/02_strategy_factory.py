from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.database import fetch_dataframe, initialize_database  # noqa: E402


initialize_database()
st.title("Strategy Factory")
specs = fetch_dataframe("SELECT * FROM strategy_specs ORDER BY created_at DESC")
if specs.empty:
    st.info("No YAML strategy specs generated yet.")
else:
    selected = st.selectbox("Strategy", specs["strategy_name"].tolist())
    row = specs[specs["strategy_name"] == selected].iloc[0]
    st.write(f"Validation: `{row['validation_status']}`")
    st.write(row["rationale"])
    st.code(row["source_yaml"], language="yaml")
    generated = fetch_dataframe("SELECT * FROM generated_strategies WHERE strategy_id = ?", (selected,))
    st.subheader("Convert-to-engine Status")
    st.dataframe(generated, use_container_width=True, hide_index=True)

