from __future__ import annotations

import json

import streamlit as st


def render_signal(decision: dict) -> None:
    st.metric("Score", int(decision.get("score", 0)))
    st.write(f"Signal: `{decision.get('signal', 'WAIT')}`")
    st.write(f"Permission: `{decision.get('permission', 'WATCHLIST')}`")
    st.write(f"Regime: `{decision.get('regime', 'unknown')}`")
    reasons = json.loads(decision.get("reasons") or "[]")
    flags = json.loads(decision.get("risk_flags") or "[]")
    st.write("Reasons")
    for reason in reasons:
        st.write(f"- {reason}")
    st.write("Risk flags")
    for flag in flags or ["No additional flags recorded."]:
        st.write(f"- {flag}")

