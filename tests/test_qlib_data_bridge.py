from __future__ import annotations

from pathlib import Path

import pandas as pd

import core.database as database
from core.database import fetch_dataframe, initialize_database, insert_dict
from qlib_brain.qlib_data_bridge import (
    build_qlib_research_features,
    export_qlib_dataset,
    load_openbb_for_qlib,
)


def test_load_openbb_for_qlib_dedupes(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    initialize_database()
    _insert_openbb_row("AAPL", "2024-01-01", "dup_a", close=100)
    _insert_openbb_row("AAPL", "2024-01-01", "dup_b", close=101)
    _insert_openbb_row("AAPL", "2024-01-02", "row_2", close=102)

    df = load_openbb_for_qlib(["AAPL"], "yfinance", "1d")

    assert len(df) == 2
    assert list(df["timestamp"]) == sorted(df["timestamp"])


def test_qlib_feature_builder_separates_future_label() -> None:
    dates = pd.date_range("2024-01-01", periods=35, freq="D")
    df = pd.DataFrame(
        {
            "symbol": "AAPL",
            "asset_class": "equity",
            "provider": "yfinance",
            "interval": "1d",
            "timestamp": dates,
            "open": range(100, 135),
            "high": range(101, 136),
            "low": range(99, 134),
            "close": range(100, 135),
            "volume": range(1000, 1035),
        }
    )

    features = build_qlib_research_features(df, horizon_days=5)

    assert "label_forward_return_5d" in features.columns
    first = features.dropna(subset=["close_return_1d"]).iloc[0]
    source = df[df["timestamp"] == first["timestamp"]].iloc[0]
    assert first["close_return_1d"] == (source["close"] / (source["close"] - 1) - 1)
    assert first["label_forward_return_5d"] > 0


def test_export_qlib_dataset_writes_files_and_db(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    initialize_database()
    for index in range(40):
        timestamp = (pd.Timestamp("2024-01-01") + pd.Timedelta(days=index)).strftime("%Y-%m-%d")
        _insert_openbb_row("AAPL", timestamp, f"aapl_{index}", close=100 + index)

    result = export_qlib_dataset(["AAPL"], output_dir=tmp_path / "qlib")

    assert result["row_count"] > 0
    assert Path(result["output_path"]).exists()
    assert Path(result["manifest_path"]).exists()
    stored = fetch_dataframe("SELECT export_id, row_count, output_path FROM qlib_dataset_exports")
    assert stored.iloc[0]["export_id"] == result["export_id"]
    assert stored.iloc[0]["row_count"] == result["row_count"]


def _insert_openbb_row(symbol: str, timestamp: str, row_id: str, close: float = 100) -> None:
    insert_dict(
        "openbb_market_data",
        {
            "id": row_id,
            "symbol": symbol,
            "asset_class": "equity",
            "provider": "yfinance",
            "interval": "1d",
            "timestamp": timestamp,
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": 1000,
            "adjusted_close": close,
            "source": "test",
            "retrieved_at": "2026-01-01T00:00:00+00:00",
            "metadata_json": "{}",
        },
    )
