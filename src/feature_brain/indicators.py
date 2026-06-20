from __future__ import annotations

import numpy as np
import pandas as pd


def rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(window).mean()
    loss = (-delta.clip(upper=0)).rolling(window).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def atr(df: pd.DataFrame, window: int = 14) -> pd.Series:
    previous_close = df["close"].shift(1)
    true_range = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - previous_close).abs(),
            (df["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.rolling(window).mean()


def macd(series: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    fast = series.ewm(span=12, adjust=False).mean()
    slow = series.ewm(span=26, adjust=False).mean()
    macd_line = fast - slow
    signal = macd_line.ewm(span=9, adjust=False).mean()
    histogram = macd_line - signal
    return macd_line, signal, histogram


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add v1 indicator set using only current and past candles."""
    out = df.sort_values("timestamp").copy()
    out["ema_20"] = out["close"].ewm(span=20, adjust=False).mean()
    out["ema_50"] = out["close"].ewm(span=50, adjust=False).mean()
    out["ema_200"] = out["close"].ewm(span=200, adjust=False).mean()
    out["sma_20"] = out["close"].rolling(20).mean()
    out["rsi_14"] = rsi(out["close"], 14)
    out["atr_14"] = atr(out, 14)
    out["bb_middle"] = out["close"].rolling(20).mean()
    bb_std = out["close"].rolling(20).std()
    out["bb_upper"] = out["bb_middle"] + 2 * bb_std
    out["bb_lower"] = out["bb_middle"] - 2 * bb_std
    out["macd"], out["macd_signal"], out["macd_hist"] = macd(out["close"])
    out["rolling_return_24"] = out["close"].pct_change(24)
    out["rolling_volatility_24"] = out["close"].pct_change().rolling(24).std()
    out["volume_sma_20"] = out["volume"].rolling(20).mean()
    volume_std = out["volume"].rolling(20).std().replace(0, np.nan)
    out["volume_zscore"] = (out["volume"] - out["volume_sma_20"]) / volume_std
    out["drawdown"] = out["close"] / out["close"].cummax() - 1
    out["liquidity_proxy"] = out["close"] * out["volume"]
    out["spread_proxy"] = (out["high"] - out["low"]) / out["close"]
    return out

