from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

import pandas as pd

from core.config_loader import load_global_config
from core.logger import get_logger
from core.paths import DATABASE_DIR, PROJECT_ROOT, resolve_project_path

try:
    import duckdb  # type: ignore
except Exception:  # pragma: no cover - depends on optional local install
    duckdb = None

logger = get_logger(__name__)
_SQLITE_FALLBACK_WARNING_EMITTED = False
SQLITE_FALLBACK_WARNING = (
    "DuckDB is not available. Falling back to SQLite. This is acceptable for local "
    "demo/research, but DuckDB is recommended for larger analytical workloads. "
    "To install DuckDB support, run: pip install -e .[database]"
)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def database_path() -> Path:
    config = load_global_config()
    return resolve_project_path(config.get("database_path", DATABASE_DIR / "trading_os.duckdb"))


@contextmanager
def connect(path: str | Path | None = None) -> Iterator[Any]:
    """Open DuckDB when available; otherwise use SQLite for local skeleton runs."""
    global duckdb
    db_path = resolve_project_path(path) if path else database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if duckdb is not None:
        try:
            connection = duckdb.connect(str(db_path))
        except Exception as exc:  # pragma: no cover - depends on local DuckDB state
            logger.warning("DuckDB connection failed; falling back to SQLite. Error type: %s", type(exc).__name__)
            duckdb = None
        else:
            try:
                yield connection
            finally:
                connection.close()
            return
    _warn_sqlite_fallback_once()
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.commit()
        connection.close()


def _warn_sqlite_fallback_once() -> None:
    global _SQLITE_FALLBACK_WARNING_EMITTED
    if not _SQLITE_FALLBACK_WARNING_EMITTED:
        logger.warning(SQLITE_FALLBACK_WARNING)
        _SQLITE_FALLBACK_WARNING_EMITTED = True


def initialize_database(path: str | Path | None = None) -> Path:
    schema_path = PROJECT_ROOT / "database" / "schema.sql"
    db_path = resolve_project_path(path) if path else database_path()
    with schema_path.open("r", encoding="utf-8") as handle:
        schema = handle.read()
    with connect(db_path) as connection:
        if duckdb is not None:
            connection.execute(schema)
        else:
            connection.executescript(schema)
        _ensure_runtime_columns(connection)
    return db_path


def _ensure_runtime_columns(connection: Any) -> None:
    """Add v1 hardening columns to databases created by earlier skeleton versions."""
    required_columns = {
        "backtest_metrics": {
            "avg_profit": "REAL",
            "best_pair": "TEXT",
            "worst_pair": "TEXT",
            "pair_level_metrics": "TEXT",
            "fee_adjusted_return": "REAL",
            "slippage_adjusted_return": "REAL",
            "parser_warnings": "TEXT",
        },
        "decisions": {
            "run_id": "TEXT",
        },
    }
    for table, columns in required_columns.items():
        existing = _table_columns(connection, table)
        for column, column_type in columns.items():
            if column not in existing:
                connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")


def _table_columns(connection: Any, table: str) -> set[str]:
    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    return {str(row[1]) for row in rows}


def fetch_dataframe(query: str, params: tuple[Any, ...] = ()) -> pd.DataFrame:
    with connect() as connection:
        if duckdb is not None:
            return connection.execute(query, params).df()
        return pd.read_sql_query(query, connection, params=params)


def execute(query: str, params: tuple[Any, ...] = ()) -> None:
    with connect() as connection:
        connection.execute(query, params)


def execute_many(query: str, rows: list[tuple[Any, ...]]) -> None:
    if not rows:
        return
    with connect() as connection:
        connection.executemany(query, rows)


def insert_dict(table: str, row: dict[str, Any]) -> None:
    columns = list(row)
    placeholders = ", ".join(["?"] * len(columns))
    column_sql = ", ".join(columns)
    values = tuple(json.dumps(value) if isinstance(value, (dict, list)) else value for value in row.values())
    with connect() as connection:
        connection.execute(f"INSERT OR REPLACE INTO {table} ({column_sql}) VALUES ({placeholders})", values)
