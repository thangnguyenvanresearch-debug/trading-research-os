from __future__ import annotations

import json

import streamlit as st


def render_risk_flags(flags_json: str) -> None:
    flags = json.loads(flags_json or "[]")
    if not flags:
        st.success("No risk flags recorded.")
        return
    for flag in flags:
        st.warning(flag)

