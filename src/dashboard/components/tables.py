from __future__ import annotations

import streamlit as st


def dataframe_or_message(df, message: str) -> None:
    if df is None or df.empty:
        st.info(message)
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

