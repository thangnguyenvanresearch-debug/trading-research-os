from __future__ import annotations

import logging

import core.database as database


def test_sqlite_fallback_warns_once(monkeypatch, tmp_path, caplog) -> None:
    monkeypatch.setattr(database, "duckdb", None)
    monkeypatch.setattr(database, "_SQLITE_FALLBACK_WARNING_EMITTED", False)
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "fallback.sqlite")
    caplog.set_level(logging.WARNING, logger="core.database")

    database.initialize_database()
    database.fetch_dataframe("SELECT * FROM assets")
    warnings = [record.message for record in caplog.records if "Falling back to SQLite" in record.message]
    assert len(warnings) == 1
