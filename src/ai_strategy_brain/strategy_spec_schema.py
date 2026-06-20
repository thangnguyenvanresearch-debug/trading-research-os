from __future__ import annotations

from typing import Any


REQUIRED_FIELDS = {
    "strategy_name",
    "asset_class",
    "engine_target",
    "timeframe",
    "pairs",
    "strategy_type",
    "regime_fit",
    "entry_logic",
    "exit_logic",
    "risk",
    "validation",
}

ALLOWED_ASSET_CLASSES = {"crypto", "equity", "etf", "multi_asset", "market_making", "arbitrage"}
ALLOWED_ENGINES = {"freqtrade", "lean", "qlib", "hummingbot", "nautilus"}
ALLOWED_OPERATORS = {">", ">=", "<", "<=", "==", "!="}
ALLOWED_LOGIC_KEYS = {"all", "any"}
ALLOWED_INDICATORS = {
    "open",
    "high",
    "low",
    "close",
    "volume",
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
}


def strategy_spec_contract() -> dict[str, Any]:
    return {
        "required_fields": sorted(REQUIRED_FIELDS),
        "allowed_asset_classes": sorted(ALLOWED_ASSET_CLASSES),
        "allowed_engines": sorted(ALLOWED_ENGINES),
        "allowed_operators": sorted(ALLOWED_OPERATORS),
        "allowed_indicators": sorted(ALLOWED_INDICATORS),
        "safety": {
            "leverage_allowed": False,
            "futures_allowed": False,
            "live_trading_allowed": False,
            "ai_may_generate_python": False,
        },
    }

