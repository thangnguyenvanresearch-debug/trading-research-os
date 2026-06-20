from __future__ import annotations

import core.database as database
from ai_strategy_brain import strategy_generator
from ai_strategy_brain.strategy_generator import generate_specs, write_specs
from data_brain import freqtrade_data_adapter
from data_brain.freqtrade_data_adapter import generate_sample_ohlcv, ingest_ohlcv
from decision_brain.decision_engine import build_decisions
from feature_brain import feature_pipeline
from feature_brain.feature_pipeline import build_features
from freqtrade_brain import batch_backtest_runner, freqtrade_strategy_converter
from freqtrade_brain.batch_backtest_runner import run_backtests
from freqtrade_brain.freqtrade_strategy_converter import convert_all_specs
from risk_brain.risk_gate import run_risk_reviews


def test_full_v1_fallback_pipeline_uses_temp_paths(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    monkeypatch.setattr(freqtrade_data_adapter, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(feature_pipeline, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(batch_backtest_runner, "REPORTS_DIR", tmp_path / "reports")
    config = {
        "runtime_paths": {
            "generated_specs": str(tmp_path / "generated" / "specs"),
            "generated_freqtrade_strategies": str(tmp_path / "generated" / "strategies"),
            "freqtrade_reports": str(tmp_path / "reports" / "freqtrade"),
        },
        "safety": {
            "live_trading_enabled": False,
            "real_orders_enabled": False,
            "leverage_enabled": False,
            "futures_enabled": False,
        },
    }
    monkeypatch.setattr(strategy_generator, "load_global_config", lambda: config)
    monkeypatch.setattr(freqtrade_strategy_converter, "load_global_config", lambda: config)
    monkeypatch.setattr(batch_backtest_runner, "load_global_config", lambda: config)

    database.initialize_database()
    ingest_ohlcv(generate_sample_ohlcv("BTC/USDT", candles=300))
    build_features()
    write_specs(generate_specs("crypto", 1, ["BTC/USDT"]))
    convert_all_specs()
    results = run_backtests()
    assert results
    run_risk_reviews()
    decisions = build_decisions()
    assert decisions
    assert all(decision["permission"] != "APPROVED_FOR_LIVE" for decision in decisions)

