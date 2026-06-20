from __future__ import annotations

import json

import core.database as database
from core.database import execute, initialize_database, insert_dict, utc_now
from core.validation import analyze_python_lookahead_risk
from risk_brain.risk_gate import review_metrics, run_risk_reviews


def test_risk_gate_rejects_weak_strategy() -> None:
    status, flags = review_metrics(
        {
            "max_drawdown": 0.5,
            "trade_count": 3,
            "profit_factor": 0.7,
            "out_of_sample_return": -0.2,
            "win_rate": 0.9,
            "avg_win": 0.01,
            "avg_loss": -0.05,
            "fee_slippage_adjusted_return": -0.1,
            "pair_concentration": 1.0,
            "regime_count": 1,
            "equity_smoothness": 0.99,
        }
    )
    assert status.value == "rejected"
    assert len(flags) >= 5


def test_risk_gate_rejects_dry_run_divergence() -> None:
    status, flags = review_metrics(
        {
            "max_drawdown": 0.05,
            "trade_count": 150,
            "profit_factor": 1.5,
            "out_of_sample_return": 0.05,
            "win_rate": 0.55,
            "avg_win": 0.02,
            "avg_loss": -0.01,
            "fee_slippage_adjusted_return": 0.10,
            "dry_run_return": -0.10,
            "pair_concentration": 0.4,
            "regime_count": 2,
            "equity_smoothness": 0.5,
        }
    )
    assert status.value == "rejected"
    assert any("diverge" in flag for flag in flags)


def test_risk_gate_rejects_lookahead_review() -> None:
    lookahead = analyze_python_lookahead_risk("dataframe['bad'] = dataframe.close.shift(-1)")
    status, flags = review_metrics(
        {
            "max_drawdown": 0.05,
            "trade_count": 150,
            "profit_factor": 1.5,
            "out_of_sample_return": 0.05,
            "win_rate": 0.55,
            "avg_win": 0.02,
            "avg_loss": -0.01,
            "fee_slippage_adjusted_return": 0.10,
            "pair_concentration": 0.4,
            "regime_count": 2,
            "equity_smoothness": 0.5,
        },
        lookahead_review={"has_lookahead_risk": lookahead["has_risk"], "issues": lookahead["risk_patterns"]},
    )
    assert status.value == "rejected"
    assert any("look-ahead" in flag for flag in flags)


def test_risk_gate_can_approve_for_dry_run_and_archive() -> None:
    strong = {
        "max_drawdown": 0.05,
        "trade_count": 150,
        "profit_factor": 1.5,
        "out_of_sample_return": 0.05,
        "win_rate": 0.55,
        "avg_win": 0.02,
        "avg_loss": -0.01,
        "fee_slippage_adjusted_return": 0.10,
        "pair_concentration": 0.4,
        "regime_count": 2,
        "equity_smoothness": 0.5,
    }
    status, _ = review_metrics(strong)
    assert status.value == "approved_for_dry_run"
    archived, _ = review_metrics({**strong, "archived": True})
    assert archived.value == "archived"


def test_risk_reviews_persist_lookahead_inspected_paths(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    initialize_database()
    generated_path = tmp_path / "generated_strategy.py"
    generated_path.write_text("dataframe['bad'] = dataframe.close.shift(-1)\n", encoding="utf-8")

    insert_dict(
        "strategy_specs",
        {
            "strategy_id": "lookahead_path_v1",
            "strategy_name": "lookahead_path_v1",
            "asset_class": "crypto",
            "engine_target": "freqtrade",
            "spec_path": "data/generated/specs/lookahead_path_v1.yaml",
            "source_yaml": "strategy_name: lookahead_path_v1\n",
            "validation_status": "valid",
            "created_at": utc_now(),
        },
    )
    insert_dict(
        "generated_strategies",
        {
            "generated_id": "gen_lookahead_path_v1",
            "strategy_id": "lookahead_path_v1",
            "engine_target": "freqtrade",
            "code_path": str(generated_path),
            "template_version": "test",
            "created_at": utc_now(),
        },
    )
    execute(
        """
        INSERT OR REPLACE INTO backtest_metrics
        (run_id, strategy_id, total_return, out_of_sample_return, max_drawdown, win_rate,
         trade_count, profit_factor, avg_win, avg_loss, fee_slippage_adjusted_return,
         pair_concentration, regime_count, equity_smoothness, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "run_lookahead_path_v1",
            "lookahead_path_v1",
            0.1,
            0.05,
            0.05,
            0.55,
            150,
            1.5,
            0.02,
            -0.01,
            0.08,
            0.4,
            2,
            0.5,
            utc_now(),
        ),
    )

    reviews = run_risk_reviews()
    assert reviews[0]["status"] == "rejected"
    flags = json.loads(reviews[0]["flags"])
    assert any("Look-ahead audit:" in flag for flag in flags)
    inspected_flags = [flag for flag in flags if flag.startswith("Look-ahead inspected path:")]
    assert inspected_flags
    assert len(inspected_flags) == len(set(inspected_flags))
    assert any(str(generated_path) in flag for flag in inspected_flags)
