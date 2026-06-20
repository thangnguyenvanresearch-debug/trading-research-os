from __future__ import annotations

from pathlib import Path

import pandas as pd


def read_table(path: str | Path) -> pd.DataFrame:
    resolved = Path(path)
    if resolved.suffix.lower() == ".parquet":
        return pd.read_parquet(resolved)
    return pd.read_csv(resolved, parse_dates=["timestamp"])


def write_table(df: pd.DataFrame, path: str | Path) -> Path:
    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    if resolved.suffix.lower() == ".parquet":
        try:
            df.to_parquet(resolved, index=False)
            return resolved
        except Exception:
            resolved = resolved.with_suffix(".csv")
    df.to_csv(resolved, index=False)
    return resolved

