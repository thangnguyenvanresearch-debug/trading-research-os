from __future__ import annotations

import json

import pandas as pd

from core.database import execute_many, fetch_dataframe, initialize_database
from core.paths import DATA_DIR
from data_brain.csv_parquet_loader import write_table
from data_brain.freqtrade_data_adapter import normalize_pair
from feature_brain.indicators import add_indicators
from feature_brain.regime_detector import detect_regimes_by_symbol


FEATURE_COLUMNS = [
    "ema_20",
    "ema_50",
    "ema_200",
    "sma_20",
    "rsi_14",
    "atr_14",
    "bb_middle",
    "bb_upper",
    "bb_lower",
    "macd",
    "macd_signal",
    "macd_hist",
    "rolling_return_24",
    "rolling_volatility_24",
    "volume_sma_20",
    "volume_zscore",
    "drawdown",
    "liquidity_proxy",
    "spread_proxy",
]


def load_market_data() -> pd.DataFrame:
    initialize_database()
    return fetch_dataframe("SELECT * FROM market_data ORDER BY symbol, timeframe, timestamp")


def build_features() -> pd.DataFrame:
    market = load_market_data()
    if market.empty:
        raise ValueError("No market data found. Run scripts/download_crypto_data.py first.")
    frames = []
    for _, group in market.groupby(["symbol", "timeframe"]):
        features = add_indicators(group)
        frames.append(features)
        symbol = str(group["symbol"].iloc[0])
        timeframe = str(group["timeframe"].iloc[0])
        write_table(features, DATA_DIR / "features" / f"{normalize_pair(symbol)}_{timeframe}_features.csv")
    combined = pd.concat(frames, ignore_index=True)
    store_features(combined)
    store_regimes(combined)
    return combined


def store_features(features: pd.DataFrame) -> None:
    rows = []
    for _, row in features.iterrows():
        for feature_name in FEATURE_COLUMNS:
            value = row.get(feature_name)
            if pd.isna(value):
                continue
            rows.append(
                (
                    row["symbol"],
                    row["timeframe"],
                    str(row["timestamp"]),
                    feature_name,
                    float(value),
                    "feature_pipeline",
                ),
            )
    execute_many(
        """
        INSERT OR REPLACE INTO features
        (symbol, timeframe, timestamp, feature_name, feature_value, source)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def store_regimes(features: pd.DataFrame) -> None:
    regimes = detect_regimes_by_symbol(features)
    rows = [
        (
                row["symbol"],
                row["timeframe"],
                str(row["timestamp"]),
                row["regime"],
                float(row["confidence"]),
                json.dumps(row["details"]),
        )
        for _, row in regimes.iterrows()
    ]
    execute_many(
        """
        INSERT OR REPLACE INTO regimes
        (symbol, timeframe, timestamp, regime, confidence, details)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
