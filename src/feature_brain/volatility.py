from __future__ import annotations

import pandas as pd


def realized_volatility(close: pd.Series, window: int = 24) -> pd.Series:
    return close.pct_change().rolling(window).std()

