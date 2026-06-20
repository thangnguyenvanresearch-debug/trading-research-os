from __future__ import annotations

import pandas as pd


REQUIRED_OHLCV_COLUMNS = {"timestamp", "open", "high", "low", "close", "volume", "symbol", "timeframe"}


def validate_ohlcv(df: pd.DataFrame) -> list[str]:
    """Return data quality warnings for an OHLCV frame."""
    warnings: list[str] = []
    missing = REQUIRED_OHLCV_COLUMNS - set(df.columns)
    if missing:
        warnings.append(f"Missing columns: {sorted(missing)}")
        return warnings
    if df.empty:
        warnings.append("Dataset is empty.")
    if df["timestamp"].duplicated().any():
        warnings.append("Duplicate timestamps detected.")
    if (df[["open", "high", "low", "close"]] <= 0).any().any():
        warnings.append("Non-positive price detected.")
    if (df["high"] < df["low"]).any():
        warnings.append("High price below low price detected.")
    if df["close"].isna().any():
        warnings.append("Missing close prices detected.")
    return warnings

