from __future__ import annotations

import json

import core.database as database
from core.database import initialize_database, insert_dict
from lean_brain.lean_data_bridge import export_lean_research_data, load_openbb_for_lean


def test_openbb_local_data_export_dedupes_and_writes_files(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    initialize_database()
    _insert_openbb_row("AAPL", "2024-01-01", "row1")
    _insert_openbb_row("AAPL", "2024-01-01", "row2")
    _insert_openbb_row("AAPL", "2024-01-02", "row3")

    loaded = load_openbb_for_lean(["AAPL"], "yfinance", "1d")
    result = export_lean_research_data(["AAPL"], "yfinance", "1d", tmp_path / "lean_data")

    assert len(loaded) == 2
    assert result["row_counts"]["AAPL"] == 2
    assert result["paths"]["AAPL"]
    assert result["manifest_path"]
    manifest = json.loads((tmp_path / "lean_data" / "data_manifest.json").read_text(encoding="utf-8"))
    assert manifest["label"] == "LEAN research bridge data"


def _insert_openbb_row(symbol: str, timestamp: str, row_id: str) -> None:
    insert_dict(
        "openbb_market_data",
        {
            "id": row_id,
            "symbol": symbol,
            "asset_class": "equity",
            "provider": "yfinance",
            "interval": "1d",
            "timestamp": timestamp,
            "open": 100,
            "high": 101,
            "low": 99,
            "close": 100,
            "volume": 1000,
            "adjusted_close": 100,
            "source": "test",
            "retrieved_at": "2026-01-01T00:00:00+00:00",
            "metadata_json": "{}",
        },
    )
