from __future__ import annotations

import json

import pytest

import core.database as database
from data_brain.freqtrade_data_adapter import (
    generate_sample_ohlcv,
    import_freqtrade_data,
    prepare_crypto_data,
)


def test_sample_data_is_labeled_sample() -> None:
    df = generate_sample_ohlcv("BTC/USDT", candles=5)
    assert set(df["source"]) == {"sample_freqtrade_adapter"}


def test_cli_mode_does_not_silently_sample(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    monkeypatch.setattr("data_brain.freqtrade_data_adapter.freqtrade_available", lambda: False)
    with pytest.raises(RuntimeError, match="use --sample"):
        prepare_crypto_data(["BTC/USDT"], "1h", use_freqtrade_cli=True)


def test_import_freqtrade_json_labels_source(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    data_dir = tmp_path / "user_data" / "data" / "binance"
    data_dir.mkdir(parents=True)
    (data_dir / "BTC_USDT-1h.json").write_text(
        json.dumps([[1700000000000, 100, 105, 95, 102, 10], [1700003600000, 102, 106, 101, 104, 11]]),
        encoding="utf-8",
    )
    paths = import_freqtrade_data(["BTC/USDT"], "1h", tmp_path / "user_data")
    assert paths
    imported = database.fetch_dataframe("SELECT DISTINCT source FROM market_data")
    assert imported["source"].tolist() == ["freqtrade_cli_import"]

