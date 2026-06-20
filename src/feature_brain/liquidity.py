from __future__ import annotations

import pandas as pd


def liquidity_proxy(close: pd.Series, volume: pd.Series) -> pd.Series:
    return close * volume

