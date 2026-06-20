from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd

import core.database as database
from core.database import fetch_dataframe, initialize_database
from data_brain import openbb_adapter
from data_brain.openbb_adapter import (
    get_openbb_status,
    ingest_openbb_market_data,
    normalize_openbb_market_data,
)
from feature_brain.openbb_feature_bridge import FEATURE_INPUT_COLUMNS, load_openbb_market_data


def test_openbb_status_missing(monkeypatch) -> None:
    monkeypatch.setattr(openbb_adapter.importlib.util, "find_spec", lambda name: None)

    status = get_openbb_status()

    assert status["engine"] == "openbb"
    assert status["installed"] is False
    assert status["status"] == "missing"
    assert status["safe_for_live"] is False


def test_openbb_normalization() -> None:
    raw = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02"],
            "open": [100.0, 101.0],
            "high": [102.0, 103.0],
            "low": [99.0, 100.0],
            "close": [101.0, 102.0],
            "volume": [1000, 1100],
            "adjusted_close": [101.0, 102.0],
        }
    )

    normalized = normalize_openbb_market_data(raw, "AAPL", "equity", "yfinance", "1d", "run_test")

    assert {
        "id",
        "symbol",
        "asset_class",
        "provider",
        "interval",
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "adjusted_close",
        "source",
        "retrieved_at",
        "metadata_json",
    }.issubset(normalized.columns)
    assert len(normalized) == 2
    assert set(normalized["symbol"]) == {"AAPL"}
    assert set(normalized["source"]) == {"openbb_adapter"}


def test_openbb_ingestion_handles_symbol_failure(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    initialize_database()

    def fetcher(**kwargs):
        if kwargs["symbol"] == "MSFT":
            raise RuntimeError("provider failed")
        return pd.DataFrame(
            {
                "date": ["2024-01-01"],
                "open": [100.0],
                "high": [101.0],
                "low": [99.0],
                "close": [100.5],
                "volume": [1000],
            }
        )

    result = ingest_openbb_market_data(
        symbols=["AAPL", "MSFT"],
        asset_class="equity",
        start_date="2024-01-01",
        interval="1d",
        provider="yfinance",
        write_db=True,
        write_parquet=False,
        fetcher=fetcher,
    )

    assert result.rows_inserted == 1
    assert result.rows_failed == 1
    assert result.errors
    stored = fetch_dataframe("SELECT symbol, provider, source FROM openbb_market_data")
    assert stored.iloc[0]["symbol"] == "AAPL"
    assert stored.iloc[0]["provider"] == "yfinance"
    assert stored.iloc[0]["source"] == "openbb_adapter"


def test_openbb_ingestion_dedupes_repeated_market_rows(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    initialize_database()

    def fetcher(**kwargs):
        return pd.DataFrame(
            {
                "date": ["2024-01-01", "2024-01-02"],
                "open": [100.0, 101.0],
                "high": [101.0, 102.0],
                "low": [99.0, 100.0],
                "close": [100.5, 101.5],
                "volume": [1000, 1100],
            }
        )

    first = ingest_openbb_market_data(
        symbols=["AAPL"],
        asset_class="equity",
        start_date="2024-01-01",
        interval="1d",
        provider="yfinance",
        write_db=True,
        write_parquet=False,
        fetcher=fetcher,
    )
    second = ingest_openbb_market_data(
        symbols=["AAPL"],
        asset_class="equity",
        start_date="2024-01-01",
        interval="1d",
        provider="yfinance",
        write_db=True,
        write_parquet=False,
        fetcher=fetcher,
    )

    stored = fetch_dataframe(
        "SELECT COUNT(*) AS rows, COUNT(DISTINCT timestamp) AS distinct_timestamps FROM openbb_market_data"
    )
    assert first.rows_inserted == 2
    assert second.rows_inserted == 0
    assert second.rows_skipped_duplicate == 2
    assert second.dedupe_enabled is True
    assert int(stored.iloc[0]["rows"]) == 2
    assert int(stored.iloc[0]["distinct_timestamps"]) == 2


def test_openbb_ingestion_rejects_provider_output_without_timestamp(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    initialize_database()

    def fetcher(**kwargs):
        return pd.DataFrame(
            {
                "open": [100.0],
                "high": [101.0],
                "low": [99.0],
                "close": [100.5],
                "volume": [1000],
            }
        )

    result = ingest_openbb_market_data(
        symbols=["AAPL"],
        asset_class="equity",
        start_date="2024-01-01",
        interval="1d",
        provider="yfinance",
        write_db=True,
        write_parquet=False,
        fetcher=fetcher,
    )

    assert result.rows_inserted == 0
    assert result.rows_failed == 1
    assert any("No timestamp-like column found" in error for error in result.errors)
    stored = fetch_dataframe("SELECT COUNT(*) AS rows FROM openbb_market_data")
    assert int(stored.iloc[0]["rows"]) == 0


def test_openbb_feature_bridge_missing_table_returns_empty_frame(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "missing_schema.sqlite")

    loaded = load_openbb_market_data(["AAPL"], "1d")

    assert loaded.empty
    assert list(loaded.columns) == FEATURE_INPUT_COLUMNS


def test_openbb_no_live_capability(monkeypatch) -> None:
    monkeypatch.setattr(openbb_adapter.importlib.util, "find_spec", lambda name: None)
    status = get_openbb_status()

    assert status["safe_for_live"] is False
    names = set(dir(openbb_adapter))
    assert not {"create_order", "place_order", "market_order", "limit_order"} & names


def test_openbb_cli_missing_package(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    scripts_dir = Path(__file__).resolve().parents[1] / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    spec = importlib.util.spec_from_file_location("ingest_openbb_data_cli", scripts_dir / "ingest_openbb_data.py")
    cli = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(cli)
    monkeypatch.setattr(cli, "detect_openbb", lambda: False)

    exit_code = cli.main(["--symbols", "AAPL", "--asset-class", "equity"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "OpenBB is not installed" in output
