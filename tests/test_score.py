from __future__ import annotations

from decision_brain.strategy_score import score_strategy


def test_score_range() -> None:
    score = score_strategy(
        {
            "out_of_sample_return": 0.08,
            "max_drawdown": 0.12,
            "profit_factor": 1.6,
            "trade_count": 80,
            "fee_slippage_adjusted_return": 0.07,
        }
    )
    assert 0 <= score <= 100

