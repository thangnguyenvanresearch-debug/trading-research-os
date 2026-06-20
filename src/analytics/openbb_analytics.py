from __future__ import annotations

import math
from typing import Any

import pandas as pd

from core.database import fetch_dataframe
from core.logger import get_logger


logger = get_logger(__name__)

PRICE_COLUMNS = [
    "symbol",
    "asset_class",
    "provider",
    "interval",
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "adjusted_close",
    "source",
    "retrieved_at",
]
SUMMARY_COLUMNS = [
    "symbol",
    "provider",
    "interval",
    "first_date",
    "last_date",
    "rows",
    "latest_close",
    "total_return",
    "annualized_volatility",
    "max_drawdown",
    "avg_volume",
    "missing_close_count",
]


def load_openbb_prices(
    symbols: list[str] | None = None,
    provider: str | None = None,
    interval: str | None = None,
) -> pd.DataFrame:
    """Load OpenBB price rows from the local database only."""
    clauses: list[str] = []
    params: list[Any] = []
    if symbols:
        clauses.append(f"symbol IN ({', '.join(['?'] * len(symbols))})")
        params.extend(symbols)
    if provider:
        clauses.append("provider = ?")
        params.append(provider)
    if interval:
        clauses.append("interval = ?")
        params.append(interval)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    try:
        df = fetch_dataframe(
            f"""
            SELECT symbol, asset_class, provider, interval, timestamp, open, high, low,
                   close, volume, adjusted_close, source, retrieved_at
            FROM openbb_market_data
            {where}
            ORDER BY symbol, timestamp
            """,
            tuple(params),
        )
    except Exception as exc:
        if _is_missing_openbb_table_error(exc):
            logger.warning("OpenBB market data table is unavailable; returning empty analytics frame.")
            return _empty_prices()
        raise
    return _prepare_prices(df)


def compute_openbb_return_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Compute descriptive return statistics by symbol from local OpenBB prices."""
    df = _prepare_prices(df)
    if df.empty:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)
    rows: list[dict[str, Any]] = []
    for symbol, group in df.groupby("symbol", sort=True):
        group = group.sort_values("timestamp")
        close = pd.to_numeric(group["close"], errors="coerce")
        valid_close = close.dropna()
        returns = valid_close.pct_change().dropna()
        first_close = float(valid_close.iloc[0]) if not valid_close.empty else math.nan
        latest_close = float(valid_close.iloc[-1]) if not valid_close.empty else math.nan
        total_return = latest_close / first_close - 1 if first_close and not math.isnan(first_close) else math.nan
        running_max = valid_close.cummax()
        drawdown = valid_close / running_max - 1
        interval = str(group["interval"].dropna().iloc[-1]) if group["interval"].notna().any() else ""
        rows.append(
            {
                "symbol": symbol,
                "provider": _latest_text(group, "provider"),
                "interval": interval,
                "first_date": group["timestamp"].min(),
                "last_date": group["timestamp"].max(),
                "rows": int(len(group)),
                "latest_close": latest_close,
                "total_return": total_return,
                "annualized_volatility": float(returns.std() * math.sqrt(252))
                if interval == "1d" and len(returns) > 1
                else math.nan,
                "max_drawdown": abs(float(drawdown.min())) if not drawdown.empty else math.nan,
                "avg_volume": float(pd.to_numeric(group["volume"], errors="coerce").mean()),
                "missing_close_count": int(close.isna().sum()),
            }
        )
    return pd.DataFrame(rows, columns=SUMMARY_COLUMNS)


def compute_openbb_pair_comparison(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Return normalized index, daily returns, and correlation matrix for local OpenBB prices."""
    df = _prepare_prices(df)
    empty = {
        "normalized_index": pd.DataFrame(columns=["timestamp", "symbol", "normalized_close"]),
        "daily_returns": pd.DataFrame(),
        "correlation_matrix": pd.DataFrame(),
    }
    if df.empty or df["symbol"].nunique() < 1:
        return empty
    pivot = (
        df.pivot_table(index="timestamp", columns="symbol", values="close", aggfunc="last")
        .sort_index()
        .dropna(how="all")
    )
    if pivot.empty:
        return empty
    base = pivot.apply(lambda col: col.dropna().iloc[0] if not col.dropna().empty else math.nan)
    normalized = pivot.divide(base).multiply(100)
    returns = pivot.pct_change(fill_method=None)
    normalized_long = (
        normalized.reset_index()
        .melt(id_vars="timestamp", var_name="symbol", value_name="normalized_close")
        .dropna(subset=["normalized_close"])
    )
    correlation = returns.corr() if pivot.shape[1] >= 2 else pd.DataFrame()
    return {
        "normalized_index": normalized_long,
        "daily_returns": returns,
        "correlation_matrix": correlation,
    }


def compute_openbb_data_quality(df: pd.DataFrame) -> dict[str, Any]:
    """Compute descriptive data-quality checks for local OpenBB market data."""
    df = _prepare_prices(df)
    if df.empty:
        return {
            "duplicate_timestamp_count": 0,
            "missing_close_count": 0,
            "non_positive_prices": 0,
            "high_below_low_count": 0,
            "date_coverage_by_symbol": pd.DataFrame(columns=["symbol", "first_date", "last_date", "rows"]),
            "provider_source_summary": pd.DataFrame(columns=["provider", "source", "rows"]),
        }
    price_columns = ["open", "high", "low", "close"]
    prices = df[price_columns].apply(pd.to_numeric, errors="coerce")
    duplicate_count = int(df.duplicated(subset=["symbol", "provider", "interval", "timestamp"]).sum())
    coverage = (
        df.groupby("symbol", as_index=False)
        .agg(first_date=("timestamp", "min"), last_date=("timestamp", "max"), rows=("timestamp", "count"))
        .sort_values("symbol")
    )
    provider_summary = (
        df.groupby(["provider", "source"], dropna=False)
        .size()
        .reset_index(name="rows")
        .sort_values(["provider", "source"])
    )
    return {
        "duplicate_timestamp_count": duplicate_count,
        "missing_close_count": int(pd.to_numeric(df["close"], errors="coerce").isna().sum()),
        "non_positive_prices": int((prices <= 0).sum().sum()),
        "high_below_low_count": int(
            (pd.to_numeric(df["high"], errors="coerce") < pd.to_numeric(df["low"], errors="coerce")).sum()
        ),
        "date_coverage_by_symbol": coverage,
        "provider_source_summary": provider_summary,
    }


def _prepare_prices(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return _empty_prices()
    prepared = df.copy()
    for column in PRICE_COLUMNS:
        if column not in prepared.columns:
            prepared[column] = pd.NA
    prepared["timestamp"] = pd.to_datetime(prepared["timestamp"], errors="coerce")
    for column in ["open", "high", "low", "close", "volume", "adjusted_close"]:
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
    return prepared.dropna(subset=["timestamp"]).sort_values(["symbol", "timestamp"]).reset_index(drop=True)


def _empty_prices() -> pd.DataFrame:
    return pd.DataFrame(columns=PRICE_COLUMNS)


def _latest_text(df: pd.DataFrame, column: str) -> str:
    values = df[column].dropna()
    return str(values.iloc[-1]) if not values.empty else ""


def _is_missing_openbb_table_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return (
        "openbb_market_data" in message
        and ("no such table" in message or "does not exist" in message or "not found" in message)
    )
