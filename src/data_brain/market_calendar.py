from __future__ import annotations

import pandas as pd


def infer_market_session(timestamp: pd.Timestamp, asset_class: str) -> str:
    """Classify a timestamp into a broad market session label."""
    if asset_class == "crypto":
        return "24_7"
    if timestamp.weekday() >= 5:
        return "closed_weekend"
    return "regular"

