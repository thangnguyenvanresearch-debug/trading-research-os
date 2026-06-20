from __future__ import annotations

from core.database import fetch_dataframe


def leaderboard():
    return fetch_dataframe(
        """
        SELECT bm.*, rr.status, rr.flags
        FROM backtest_metrics bm
        LEFT JOIN risk_reviews rr ON rr.run_id = bm.run_id
        ORDER BY fee_slippage_adjusted_return DESC
        """
    )

