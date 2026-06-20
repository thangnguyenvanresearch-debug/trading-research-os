from __future__ import annotations

import pandas as pd


def detect_latest_regime(features: pd.DataFrame) -> tuple[str, dict[str, float]]:
    """Classify the latest market condition with transparent heuristic rules."""
    if features.empty:
        return "unknown", {}
    latest = features.dropna().iloc[-1] if not features.dropna().empty else features.iloc[-1]
    close = float(latest.get("close", 0))
    ema_50 = float(latest.get("ema_50", close))
    ema_200 = float(latest.get("ema_200", close))
    vol = float(latest.get("rolling_volatility_24", 0) or 0)
    spread = float(latest.get("spread_proxy", 0) or 0)
    volume_z = float(latest.get("volume_zscore", 0) or 0)

    parts: list[str] = []
    if close > ema_50 > ema_200:
        parts.append("uptrend")
    elif close < ema_50 < ema_200:
        parts.append("downtrend")
    else:
        parts.append("range")

    if vol > 0.035:
        parts.append("high_volatility")
    elif vol < 0.012:
        parts.append("low_volatility")
    else:
        parts.append("medium_volatility")

    if abs(volume_z) > 1.5 and vol > 0.02:
        parts.append("breakout_candidate")
    if parts[0] == "range" and vol < 0.02:
        parts.append("mean_reversion_candidate")
    if spread > 0.03:
        parts.append("illiquid_avoid")

    return "_".join(parts), {"volatility": vol, "spread_proxy": spread, "volume_zscore": volume_z}


def detect_regimes_by_symbol(features: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (symbol, timeframe), group in features.groupby(["symbol", "timeframe"]):
        regime, details = detect_latest_regime(group)
        rows.append(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": group["timestamp"].max(),
                "regime": regime,
                "confidence": 0.70,
                "details": details,
            }
        )
    return pd.DataFrame(rows)

