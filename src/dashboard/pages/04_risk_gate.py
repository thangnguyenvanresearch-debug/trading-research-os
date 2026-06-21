from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.database import fetch_dataframe, initialize_database  # noqa: E402
from dashboard.components.risk_panels import render_risk_flags  # noqa: E402
from dashboard.components.ui import caveat_box, compact_dataframe, hero, metric_card, section_header, setup_page  # noqa: E402


initialize_database()
setup_page()
hero(
    "Risk Gate",
    "Review whether a research candidate is eligible for further dry-run evaluation. No live approval exists here.",
    badges=[("Research gate", "info"), ("Live disabled", "success")],
)
reviews = fetch_dataframe("SELECT * FROM risk_reviews ORDER BY reviewed_at DESC")
if reviews.empty:
    st.info("No risk reviews yet.")
else:
    selected = st.selectbox("Review", reviews["review_id"].tolist())
    row = reviews[reviews["review_id"] == selected].iloc[0]
    display_status = "Rejected by Risk Gate" if row["status"] == "rejected" else str(row["status"])
    cards = st.columns(3)
    with cards[0]:
        metric_card("Selected Review", selected, ("Local record", "neutral"))
    with cards[1]:
        metric_card("Strategy", row["strategy_id"], ("Candidate", "info"))
    with cards[2]:
        metric_card("Risk Gate Result", display_status, ("Blocked" if row["status"] == "rejected" else "Research only", "danger" if row["status"] == "rejected" else "warning"))
    section_header("Risk Flags")
    render_risk_flags(row["flags"])
    if row["status"] == "approved_for_dry_run":
        caveat_box("Approved for dry-run research only. Live trading remains disabled.", "warning")
    elif row["status"] == "rejected":
        caveat_box("Rejected by Risk Gate. This candidate is not eligible even for paper or dry-run review until its flags are resolved.", "danger")
    with st.expander("All risk review records", expanded=False):
        compact_dataframe(reviews, height=320)
