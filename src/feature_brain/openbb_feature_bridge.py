from __future__ import annotations

import pandas as pd

from core.logger import get_logger
from core.database import fetch_dataframe


logger = get_logger(__name__)
FEATURE_INPUT_COLUMNS = ["symbol", "timeframe", "timestamp", "open", "high", "low", "close", "volume", "source"]


def load_openbb_market_data(symbols: list[str] | None = None, interval: str = "1d") -> pd.DataFrame:
    """Load normalized OpenBB OHLCV rows from local storage.

    This bridge intentionally reads only from the local database. It does not call OpenBB or any
    external provider, so feature workflows can remain deterministic once ingestion is complete.
    """
    try:
        if symbols:
            placeholders = ", ".join(["?"] * len(symbols))
            return fetch_dataframe(
                f"""
                SELECT *
                FROM openbb_market_data
                WHERE symbol IN ({placeholders}) AND interval = ?
                ORDER BY symbol, timestamp
                """,
                tuple(symbols) + (interval,),
            )
        return fetch_dataframe(
            """
            SELECT *
            FROM openbb_market_data
            WHERE interval = ?
            ORDER BY symbol, timestamp
            """,
            (interval,),
        )
    except Exception as exc:
        if _is_missing_openbb_table_error(exc):
            logger.warning("OpenBB market data table is unavailable; returning empty feature input frame.")
            return _empty_feature_input()
        raise


def convert_openbb_to_feature_input(df: pd.DataFrame) -> pd.DataFrame:
    """Convert OpenBB market rows into the common OHLCV feature input shape.

    Limitations:
    - This does not merge OpenBB rows into the primary `market_data` table.
    - Corporate actions, adjusted prices, and provider-specific metadata remain separate.
    - Callers should still run data quality checks before using the output for research.
    """
    if df.empty:
        return _empty_feature_input()
    converted = df.rename(columns={"interval": "timeframe"}).copy()
    converted["source"] = converted.get("source", "openbb_adapter")
    return converted[FEATURE_INPUT_COLUMNS]


def _empty_feature_input() -> pd.DataFrame:
    return pd.DataFrame(columns=FEATURE_INPUT_COLUMNS)


def _is_missing_openbb_table_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return (
        "openbb_market_data" in message
        and ("no such table" in message or "does not exist" in message or "not found" in message)
    )
