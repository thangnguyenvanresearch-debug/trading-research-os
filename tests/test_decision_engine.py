from __future__ import annotations

import json

import yaml

import core.database as database
from core.database import execute, initialize_database, insert_dict, utc_now
from decision_brain.decision_engine import build_decisions


def test_decisions_are_per_symbol_and_not_truncated(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    initialize_database()
    spec = {
        "strategy_name": "multi_pair_v1",
        "asset_class": "crypto",
        "engine_target": "freqtrade",
        "timeframe": "1h",
        "pairs": ["ETH/USDT", "SOL/USDT"],
        "strategy_type": "test",
        "regime_fit": ["uptrend"],
        "entry_logic": {"all": []},
        "exit_logic": {"any": []},
        "risk": {"leverage_allowed": False, "futures_allowed": False},
        "validation": {"require_fee_model": True, "require_slippage_model": True},
    }
    insert_dict(
        "strategy_specs",
        {
            "strategy_id": "multi_pair_v1",
            "strategy_name": "multi_pair_v1",
            "asset_class": "crypto",
            "engine_target": "freqtrade",
            "spec_path": "test.yaml",
            "source_yaml": yaml.safe_dump(spec),
            "validation_status": "valid",
            "created_at": utc_now(),
        },
    )
    execute(
        """
        INSERT OR REPLACE INTO backtest_metrics
        (run_id, strategy_id, total_return, out_of_sample_return, max_drawdown, win_rate,
         trade_count, profit_factor, avg_win, avg_loss, fee_slippage_adjusted_return,
         pair_concentration, regime_count, equity_smoothness, created_at, pair_level_metrics)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "run1",
            "multi_pair_v1",
            0.1,
            0.05,
            0.1,
            0.5,
            120,
            1.5,
            0.02,
            -0.01,
            0.08,
            0.5,
            2,
            0.5,
            utc_now(),
            json.dumps({"ETH/USDT": {}, "SOL/USDT": {}}),
        ),
    )
    insert_dict(
        "risk_reviews",
        {
            "review_id": "risk_run1",
            "strategy_id": "multi_pair_v1",
            "run_id": "run1",
            "status": "paper_only",
            "flags": "[]",
            "reviewed_at": utc_now(),
        },
    )
    decisions = build_decisions()
    assert {decision["symbol"] for decision in decisions} == {"ETH/USDT", "SOL/USDT"}
    build_decisions()
    stored = database.fetch_dataframe("SELECT * FROM decisions")
    assert len(stored) == 2

