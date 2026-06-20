from __future__ import annotations

import sys

import pandas as pd

from analytics import openbb_analytics
from analytics.openbb_analytics import (
    compute_openbb_data_quality,
    compute_openbb_pair_comparison,
    compute_openbb_return_summary,
)


def test_openbb_return_summary_on_mock_local_data() -> None:
    df = _mock_prices()

    summary = compute_openbb_return_summary(df)

    aapl = summary[summary["symbol"] == "AAPL"].iloc[0]
    assert aapl["rows"] == 3
    assert aapl["latest_close"] == 90.0
    assert round(float(aapl["total_return"]), 4) == -0.1
    assert aapl["avg_volume"] == 1100.0


def test_openbb_max_drawdown_calculation() -> None:
    summary = compute_openbb_return_summary(_mock_prices())

    aapl = summary[summary["symbol"] == "AAPL"].iloc[0]

    assert round(float(aapl["max_drawdown"]), 4) == 0.2


def test_openbb_data_quality_catches_duplicate_timestamp() -> None:
    df = pd.concat([_mock_prices(), _mock_prices().iloc[[0]]], ignore_index=True)

    quality = compute_openbb_data_quality(df)

    assert quality["duplicate_timestamp_count"] == 1
    assert quality["missing_close_count"] == 0
    assert not quality["provider_source_summary"].empty


def test_openbb_empty_input_returns_safe_outputs() -> None:
    empty = pd.DataFrame()

    summary = compute_openbb_return_summary(empty)
    comparison = compute_openbb_pair_comparison(empty)
    quality = compute_openbb_data_quality(empty)

    assert summary.empty
    assert list(summary.columns)
    assert comparison["normalized_index"].empty
    assert comparison["daily_returns"].empty
    assert comparison["correlation_matrix"].empty
    assert quality["duplicate_timestamp_count"] == 0
    assert quality["date_coverage_by_symbol"].empty


def test_openbb_pair_comparison_returns_index_and_correlation() -> None:
    comparison = compute_openbb_pair_comparison(_mock_prices())

    assert not comparison["normalized_index"].empty
    assert "AAPL" in comparison["correlation_matrix"].columns
    assert "MSFT" in comparison["correlation_matrix"].columns


def test_openbb_analytics_has_no_external_openbb_or_order_surface() -> None:
    names = set(dir(openbb_analytics))

    assert "openbb" not in sys.modules
    assert not {"create_order", "place_order", "market_order", "limit_order"} & names


def _mock_prices() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "symbol": ["AAPL", "AAPL", "AAPL", "MSFT", "MSFT", "MSFT"],
            "asset_class": ["equity"] * 6,
            "provider": ["yfinance"] * 6,
            "interval": ["1d"] * 6,
            "timestamp": [
                "2024-01-01",
                "2024-01-02",
                "2024-01-03",
                "2024-01-01",
                "2024-01-02",
                "2024-01-03",
            ],
            "open": [100, 80, 90, 50, 55, 60],
            "high": [101, 82, 92, 51, 56, 61],
            "low": [99, 79, 89, 49, 54, 59],
            "close": [100, 80, 90, 50, 55, 60],
            "volume": [1000, 1100, 1200, 2000, 2100, 2200],
            "adjusted_close": [100, 80, 90, 50, 55, 60],
            "source": ["openbb_adapter"] * 6,
            "retrieved_at": ["2026-01-01T00:00:00+00:00"] * 6,
        }
    )
