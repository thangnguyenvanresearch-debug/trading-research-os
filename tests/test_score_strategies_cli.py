from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import core.database as database
from core.database import execute, initialize_database, insert_dict


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

spec = importlib.util.spec_from_file_location("score_strategies_cli", SCRIPTS_DIR / "score_strategies.py")
score_strategies = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(score_strategies)


def test_latest_only_filters_console_output_and_preserves_history(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    initialize_database()
    _insert_strategy("demo_strategy_v1")
    _insert_metrics("run_old", "demo_strategy_v1", "2026-01-01T00:00:00+00:00")
    _insert_metrics("run_new", "demo_strategy_v1", "2026-01-02T00:00:00+00:00")

    score_strategies.main(["--latest-only"])

    output = capsys.readouterr().out
    assert "run_id=run_new" in output
    assert "run_id=run_old" not in output
    assert "Summary: decisions=1" in output
    stored = database.fetch_dataframe("SELECT run_id FROM decisions ORDER BY run_id")
    assert set(stored["run_id"]) == {"run_old", "run_new"}


def test_run_id_filter_handles_missing_run_without_crashing(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    initialize_database()
    _insert_strategy("demo_strategy_v1")
    _insert_metrics("run_existing", "demo_strategy_v1", "2026-01-01T00:00:00+00:00")

    score_strategies.main(["--run-id", "missing_run"])

    output = capsys.readouterr().out
    assert "No decisions found for run_id=missing_run" in output
    assert "Summary: decisions=0" in output
    stored = database.fetch_dataframe("SELECT run_id FROM decisions")
    assert set(stored["run_id"]) == {"run_existing"}


def _insert_strategy(strategy_id: str) -> None:
    insert_dict(
        "strategy_specs",
        {
            "strategy_id": strategy_id,
            "strategy_name": strategy_id,
            "asset_class": "crypto",
            "engine_target": "freqtrade",
            "spec_path": f"data/generated/specs/{strategy_id}.yaml",
            "source_yaml": (
                f"strategy_name: {strategy_id}\n"
                "pairs:\n"
                "  - ETH/USDT\n"
                "regime_fit:\n"
                "  - uptrend\n"
            ),
            "validation_status": "valid",
            "created_at": "2026-01-01T00:00:00+00:00",
        },
    )


def _insert_metrics(run_id: str, strategy_id: str, created_at: str) -> None:
    execute(
        """
        INSERT OR REPLACE INTO backtest_metrics
        (run_id, strategy_id, total_return, out_of_sample_return, max_drawdown, win_rate,
         trade_count, profit_factor, avg_win, avg_loss, fee_slippage_adjusted_return,
         pair_concentration, regime_count, equity_smoothness, created_at, pair_level_metrics)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            strategy_id,
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
            created_at,
            '{"ETH/USDT": {}}',
        ),
    )
