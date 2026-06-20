from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def price_chart(df: pd.DataFrame, title: str) -> None:
    if df.empty:
        st.info("No price data available yet.")
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

