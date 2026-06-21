from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.database import fetch_dataframe, initialize_database  # noqa: E402
from dashboard.components.risk_panels import render_risk_flags  # noqa: E402


initialize_database()
st.title("Risk Gate")
reviews = fetch_dataframe("SELECT * FROM risk_reviews ORDER BY reviewed_at DESC")
if reviews.empty:
    st.info("No risk reviews yet.")
else:
    selected = st.selectbox("Review", reviews["review_id"].tolist())
    row = reviews[reviews["review_id"] == selected].iloc[0]
    st.write(f"Strategy: `{row['strategy_id']}`")
    display_status = "Rejected by Risk Gate" if row["status"] == "rejected" else str(row["status"])
    st.write(f"Risk Gate Result: `{display_status}`")
    render_risk_flags(row["flags"])
    if row["status"] == "approved_for_dry_run":
        st.info("Approved for dry-run only. Live trading remains disabled.")
    elif row["status"] == "rejected":
        st.info("Rejected by Risk Gate. This research candidate must not enter paper/dry-run review until flags are resolved.")
    with st.expander("All risk review records", expanded=False):
        st.dataframe(reviews, use_container_width=True, hide_index=True, height=320)
