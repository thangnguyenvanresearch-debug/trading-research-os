from __future__ import annotations

import pandas as pd
import streamlit as st

try:
    import plotly.graph_objects as go
except ImportError:  # Optional visual enhancement; native Streamlit remains available.
    go = None


def plotly_available() -> bool:
    return go is not None


def price_chart(df: pd.DataFrame, title: str) -> None:
    if df.empty:
        st.info("No price data available yet.")
        return
    if go is None:
        st.warning("Plotly is not installed; showing native Streamlit fallback.")
        chart_columns = [column for column in ["close", "ema_20", "ema_50", "ema_200"] if column in df]
        native = df[["timestamp", *chart_columns]].copy().set_index("timestamp")
        st.caption(title)
        st.line_chart(native, use_container_width=True)
        with st.expander("Price details", expanded=False):
            detail_columns = [
                column
                for column in ["timestamp", "open", "high", "low", "close", "volume"]
                if column in df
            ]
            st.dataframe(df[detail_columns].tail(100), use_container_width=True, hide_index=True, height=280)
        return
    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=df["timestamp"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="Price",
        )
    )
    for col in ["ema_20", "ema_50", "ema_200"]:
        if col in df:
            fig.add_trace(go.Scatter(x=df["timestamp"], y=df[col], mode="lines", name=col))
    fig.update_layout(title=title, height=420, margin=dict(l=10, r=10, t=45, b=10))
    st.plotly_chart(fig, use_container_width=True)
