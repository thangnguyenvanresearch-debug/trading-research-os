from __future__ import annotations

import yaml

from core.config_loader import load_global_config
from core.database import insert_dict, utc_now
from core.paths import resolve_project_path
from ai_strategy_brain.strategy_spec_validator import validate_strategy_spec


def _base_risk() -> dict:
    return {
        "stop_loss": -0.03,
        "take_profit": 0.06,
        "trailing_stop": True,
        "max_open_trades": 3,
        "max_pair_exposure": 0.25,
        "leverage_allowed": False,
        "futures_allowed": False,
    }


def _base_validation() -> dict:
    return {
        "min_trades": 50,
        "max_drawdown_limit": 0.20,
        "require_out_of_sample": True,
        "require_fee_model": True,
        "require_slippage_model": True,
    }


CRYPTO_TEMPLATES: list[dict] = [
    {
        "strategy_name": "trend_pullback_rsi_atr_v1",
        "asset_class": "crypto",
        "engine_target": "freqtrade",
        "timeframe": "1h",
        "strategy_type": "trend_pullback",
        "regime_fit": ["uptrend", "medium_volatility"],
        "entry_logic": {
            "all": [
                {"indicator": "close", "operator": ">", "value": "ema_200"},
                {"indicator": "rsi_14", "operator": "<", "value": 40},
                {"indicator": "volume", "operator": ">", "value": "volume_sma_20"},
            ]
        },
        "exit_logic": {
            "any": [
                {"indicator": "rsi_14", "operator": ">", "value": 65},
                {"indicator": "close", "operator": "<", "value": "ema_50"},
            ]
        },
        "rationale": "Looks for pullbacks inside a broader uptrend with volume confirmation.",
    },
    {
        "strategy_name": "breakout_momentum_volume_v1",
        "asset_class": "crypto",
        "engine_target": "freqtrade",
        "timeframe": "1h",
        "strategy_type": "breakout_momentum",
        "regime_fit": ["breakout_candidate", "high_volatility"],
        "entry_logic": {
            "all": [
                {"indicator": "close", "operator": ">", "value": "bb_upper"},
                {"indicator": "macd", "operator": ">", "value": "macd_signal"},
                {"indicator": "volume_zscore", "operator": ">", "value": 1.0},
            ]
        },
        "exit_logic": {
            "any": [
                {"indicator": "close", "operator": "<", "value": "sma_20"},
                {"indicator": "rsi_14", "operator": ">", "value": 78},
            ]
        },
        "rationale": "Tests whether volatility expansion plus volume confirms continuation.",
    },
    {
        "strategy_name": "mean_reversion_bollinger_rsi_v1",
        "asset_class": "crypto",
        "engine_target": "freqtrade",
        "timeframe": "1h",
        "strategy_type": "mean_reversion",
        "regime_fit": ["range", "mean_reversion_candidate"],
        "entry_logic": {
            "all": [
                {"indicator": "close", "operator": "<", "value": "bb_lower"},
                {"indicator": "rsi_14", "operator": "<", "value": 32},
                {"indicator": "spread_proxy", "operator": "<", "value": 0.025},
            ]
        },
        "exit_logic": {
            "any": [
                {"indicator": "close", "operator": ">", "value": "bb_middle"},
                {"indicator": "rsi_14", "operator": ">", "value": 55},
            ]
        },
        "rationale": "Attempts to fade stretched moves only when liquidity proxy is acceptable.",
    },
    {
        "strategy_name": "volatility_breakout_atr_v1",
        "asset_class": "crypto",
        "engine_target": "freqtrade",
        "timeframe": "1h",
        "strategy_type": "volatility_breakout",
        "regime_fit": ["breakout_candidate", "medium_volatility"],
        "entry_logic": {
            "all": [
                {"indicator": "close", "operator": ">", "value": "ema_50"},
                {"indicator": "atr_14", "operator": ">", "value": "sma_20"},
                {"indicator": "volume", "operator": ">", "value": "volume_sma_20"},
            ]
        },
        "exit_logic": {
            "any": [
                {"indicator": "close", "operator": "<", "value": "ema_20"},
                {"indicator": "drawdown", "operator": "<", "value": -0.08},
            ]
        },
        "rationale": "Uses ATR expansion as a volatility-breakout proxy under trend support.",
    },
    {
        "strategy_name": "multi_timeframe_trend_confirm_v1",
        "asset_class": "crypto",
        "engine_target": "freqtrade",
        "timeframe": "1h",
        "strategy_type": "multi_timeframe_trend_confirmation",
        "regime_fit": ["uptrend", "low_volatility"],
        "entry_logic": {
            "all": [
                {"indicator": "ema_20", "operator": ">", "value": "ema_50"},
                {"indicator": "ema_50", "operator": ">", "value": "ema_200"},
                {"indicator": "rsi_14", "operator": ">", "value": 50},
            ]
        },
        "exit_logic": {
            "any": [
                {"indicator": "ema_20", "operator": "<", "value": "ema_50"},
                {"indicator": "rsi_14", "operator": "<", "value": 45},
            ]
        },
        "rationale": "A conservative trend-confirmation template for spot-only research.",
    },
    {
        "strategy_name": "rsi_bollinger_atr_guard_v1",
        "asset_class": "crypto",
        "engine_target": "freqtrade",
        "timeframe": "1h",
        "strategy_type": "rsi_bollinger_atr",
        "regime_fit": ["range", "medium_volatility"],
        "entry_logic": {
            "all": [
                {"indicator": "rsi_14", "operator": "<", "value": 35},
                {"indicator": "close", "operator": "<", "value": "bb_middle"},
                {"indicator": "rolling_volatility_24", "operator": "<", "value": 0.05},
            ]
        },
        "exit_logic": {
            "any": [
                {"indicator": "rsi_14", "operator": ">", "value": 62},
                {"indicator": "close", "operator": ">", "value": "bb_upper"},
            ]
        },
        "rationale": "Combines RSI and Bollinger mean-reversion with a volatility guard.",
    },
]


def generate_specs(asset_class: str, count: int, pairs: list[str]) -> list[dict]:
    if asset_class != "crypto":
        return [equity_factor_placeholder(pairs)]
    specs = []
    for template in CRYPTO_TEMPLATES[: max(1, count)]:
        spec = {
            **template,
            "pairs": pairs,
            "risk": _base_risk(),
            "validation": _base_validation(),
            "rejection_criteria": [
                "Reject if fee/slippage-adjusted performance is negative.",
                "Reject if result is concentrated in one pair or one extreme regime.",
                "Reject if out-of-sample performance fails configured thresholds.",
            ],
        }
        specs.append(spec)
    return specs


def equity_factor_placeholder(pairs: list[str]) -> dict:
    return {
        "strategy_name": "monthly_momentum_risk_parity_lite_v1",
        "asset_class": "etf",
        "engine_target": "lean",
        "timeframe": "1d",
        "pairs": pairs or ["SPY", "QQQ", "TLT"],
        "strategy_type": "monthly_rebalance",
        "regime_fit": ["uptrend", "low_volatility"],
        "entry_logic": {"all": [{"indicator": "rolling_return_24", "operator": ">", "value": 0}]},
        "exit_logic": {"any": [{"indicator": "drawdown", "operator": "<", "value": -0.10}]},
        "risk": _base_risk(),
        "validation": _base_validation(),
        "rationale": "Placeholder LEAN/Qlib-ready ETF factor spec for phase 3.",
        "rejection_criteria": ["Reject if benchmark comparison is unfavorable after costs."],
    }


def write_specs(specs: list[dict]) -> list[str]:
    runtime_paths = load_global_config().get("runtime_paths", {})
    output_dir = resolve_project_path(runtime_paths.get("generated_specs", "data/generated/specs"))
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    for spec in specs:
        valid, errors = validate_strategy_spec(spec)
        path = output_dir / f"{spec['strategy_name']}.yaml"
        source_yaml = yaml.safe_dump(spec, sort_keys=False)
        path.write_text(source_yaml, encoding="utf-8")
        paths.append(str(path))
        insert_dict(
            "strategy_specs",
            {
                "strategy_id": spec["strategy_name"],
                "strategy_name": spec["strategy_name"],
                "asset_class": spec["asset_class"],
                "engine_target": spec["engine_target"],
                "spec_path": str(path),
                "source_yaml": source_yaml,
                "rationale": spec.get("rationale", ""),
                "validation_status": "valid" if valid else "invalid: " + "; ".join(errors),
                "created_at": utc_now(),
                "latest_review_at": utc_now(),
            },
        )
    return paths
