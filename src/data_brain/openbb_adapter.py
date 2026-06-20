from __future__ import annotations

import importlib
import importlib.util
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from core.config_loader import load_config
from core.database import execute, fetch_dataframe, insert_dict, new_id, utc_now
from core.engine_status import OptionalEngineStatus, optional_engine_status
from core.logger import get_logger
from core.paths import DATA_DIR
from data_brain.data_quality_checks import validate_ohlcv


logger = get_logger(__name__)
OPENBB_SOURCE = "openbb_adapter"
MARKET_DATA_DIR = DATA_DIR / "openbb" / "market_data"
MACRO_DATA_DIR = DATA_DIR / "openbb" / "macro_data"


@dataclass
class OpenBBIngestionResult:
    run_id: str
    status: str
    rows_inserted: int = 0
    rows_failed: int = 0
    rows_skipped_duplicate: int = 0
    rows_updated: int = 0
    dedupe_enabled: bool = True
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    provider_summary: dict[str, Any] = field(default_factory=dict)
    output_paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "rows_inserted": self.rows_inserted,
            "rows_failed": self.rows_failed,
            "rows_skipped_duplicate": self.rows_skipped_duplicate,
            "rows_updated": self.rows_updated,
            "dedupe_enabled": self.dedupe_enabled,
            "warnings": self.warnings,
            "errors": self.errors,
            "provider_summary": self.provider_summary,
            "output_paths": self.output_paths,
        }


def detect_openbb() -> bool:
    """Return whether an OpenBB package is importable without importing provider modules."""
    return importlib.util.find_spec("openbb") is not None


def get_openbb_status() -> OptionalEngineStatus:
    installed = detect_openbb()
    return optional_engine_status(
        engine="openbb",
        installed=installed,
        status="partial" if installed else "missing",
        role="Market data, macro data, and research context layer. It is never an execution engine.",
        current_capability=(
            "OpenBB package detected; adapter can attempt market/macro ingestion into local storage."
            if installed
            else "OpenBB package is not installed; local context can only use previously ingested data."
        ),
        next_step=(
            "Run scripts/ingest_openbb_data.py with a no-key provider such as yfinance."
            if installed
            else "Install optional OpenBB support, or keep using the Freqtrade/sample workflow."
        ),
    )


@dataclass
class OpenBBAdapter:
    """Optional OpenBB research connector.

    OpenBB is used only for research/context ingestion. This adapter never places orders and
    never creates broker or exchange execution configuration.
    """

    enabled: bool = False

    def available(self) -> bool:
        return detect_openbb()

    def fetch_context(self, symbol: str) -> dict[str, Any]:
        if not self.enabled or not self.available():
            return {
                "symbol": symbol,
                "status": "openbb_not_enabled_or_not_installed",
                "message": "Install and enable OpenBB to enrich market context.",
            }
        context = get_openbb_research_context([symbol], [], include_macro=False)
        if context:
            return {"symbol": symbol, "status": "local_context_available", "context": context}
        return {
            "symbol": symbol,
            "status": "openbb_context_unavailable",
            "message": "Install OpenBB and ingest data, or ingest local OpenBB data first.",
        }


def ingest_openbb_market_data(
    symbols: list[str],
    asset_class: str,
    start_date: str,
    end_date: str | None = None,
    interval: str = "1d",
    provider: str | None = None,
    write_db: bool = True,
    write_parquet: bool = True,
    fetcher: Callable[..., Any] | None = None,
) -> OpenBBIngestionResult:
    """Fetch and normalize OpenBB OHLCV data for local research storage."""
    run_id = new_id("openbb")
    started_at = utc_now()
    result = OpenBBIngestionResult(run_id=run_id, status="running")
    requested = {
        "symbols": symbols,
        "asset_class": asset_class,
        "start_date": start_date,
        "end_date": end_date,
        "interval": interval,
        "provider": provider,
    }
    provider_name = provider or _default_provider(asset_class)
    if not symbols:
        result.status = "failed"
        result.errors.append("No symbols requested.")
        _record_ingestion_run(result, started_at, requested)
        return result
    if fetcher is None and not detect_openbb():
        result.status = "missing_openbb"
        result.warnings.append(
            "OpenBB is not installed. Install optional OpenBB support or keep using the Freqtrade/sample workflow."
        )
        _record_ingestion_run(result, started_at, requested)
        return result

    frames: list[pd.DataFrame] = []
    for symbol in symbols:
        try:
            raw = fetcher(
                symbol=symbol,
                asset_class=asset_class,
                start_date=start_date,
                end_date=end_date,
                interval=interval,
                provider=provider_name,
            ) if fetcher else _fetch_openbb_market_data(
                symbol=symbol,
                asset_class=asset_class,
                start_date=start_date,
                end_date=end_date,
                interval=interval,
                provider=provider_name,
            )
            normalized = normalize_openbb_market_data(raw, symbol, asset_class, provider_name, interval, run_id)
            quality_warnings = validate_ohlcv(
                normalized.rename(columns={"interval": "timeframe"})[
                    ["symbol", "timeframe", "timestamp", "open", "high", "low", "close", "volume"]
                ]
            )
            result.warnings.extend([f"{symbol}: {warning}" for warning in quality_warnings])
            if normalized.empty:
                result.rows_failed += 1
                result.warnings.append(f"{symbol}: OpenBB returned no rows.")
                continue
            frames.append(normalized)
            result.provider_summary.setdefault(provider_name, {"symbols": [], "rows": 0})
            result.provider_summary[provider_name]["symbols"].append(symbol)
            result.provider_summary[provider_name]["rows"] += len(normalized)
            logger.info(
                "OpenBB normalized market data: symbol=%s asset_class=%s provider=%s interval=%s rows=%s",
                symbol,
                asset_class,
                provider_name,
                interval,
                len(normalized),
            )
        except Exception as exc:
            result.rows_failed += 1
            message = f"{symbol}: {type(exc).__name__}: {_safe_error(exc)}"
            result.errors.append(message)
            logger.warning("OpenBB market ingestion failed for %s: %s", symbol, type(exc).__name__)

    if frames:
        combined = pd.concat(frames, ignore_index=True)
        if write_db:
            store_result = _store_market_data(combined)
            result.rows_inserted = store_result["rows_inserted"]
            result.rows_skipped_duplicate = store_result["rows_skipped_duplicate"]
            result.rows_updated = store_result["rows_updated"]
            result.dedupe_enabled = store_result["dedupe_enabled"]
            result.provider_summary["_dedupe"] = {
                "enabled": result.dedupe_enabled,
                "rows_inserted": result.rows_inserted,
                "rows_skipped_duplicate": result.rows_skipped_duplicate,
                "rows_updated": result.rows_updated,
            }
        else:
            result.rows_inserted = len(combined)
        if write_parquet:
            result.output_paths.extend(_write_frame(combined, MARKET_DATA_DIR, f"{run_id}_{asset_class}_{provider_name}"))
        result.status = "completed_with_warnings" if result.errors or result.warnings else "completed"
    elif result.status == "running":
        result.status = "failed"
    _record_ingestion_run(result, started_at, requested)
    return result


def ingest_openbb_macro_data(
    indicators: list[str],
    start_date: str,
    end_date: str | None = None,
    provider: str | None = None,
    write_db: bool = True,
    write_parquet: bool = True,
    fetcher: Callable[..., Any] | None = None,
) -> OpenBBIngestionResult:
    """Best-effort OpenBB macro ingestion. Provider credential failures become warnings."""
    run_id = new_id("openbb_macro")
    started_at = utc_now()
    result = OpenBBIngestionResult(run_id=run_id, status="running")
    provider_name = provider or _default_provider("macro")
    requested = {
        "indicators": indicators,
        "start_date": start_date,
        "end_date": end_date,
        "provider": provider_name,
    }
    if not indicators:
        result.status = "failed"
        result.errors.append("No macro indicators requested.")
        _record_ingestion_run(result, started_at, requested)
        return result
    if fetcher is None and not detect_openbb():
        result.status = "missing_openbb"
        result.warnings.append("OpenBB is not installed; macro ingestion skipped.")
        _record_ingestion_run(result, started_at, requested)
        return result

    frames: list[pd.DataFrame] = []
    for indicator in indicators:
        try:
            raw = fetcher(
                indicator=indicator,
                start_date=start_date,
                end_date=end_date,
                provider=provider_name,
            ) if fetcher else _fetch_openbb_macro_data(indicator, start_date, end_date, provider_name)
            normalized = normalize_openbb_macro_data(raw, indicator, provider_name, run_id)
            if normalized.empty:
                result.rows_failed += 1
                result.warnings.append(f"{indicator}: OpenBB returned no macro rows.")
                continue
            frames.append(normalized)
            result.provider_summary.setdefault(provider_name, {"indicators": [], "rows": 0})
            result.provider_summary[provider_name]["indicators"].append(indicator)
            result.provider_summary[provider_name]["rows"] += len(normalized)
        except Exception as exc:
            result.rows_failed += 1
            result.warnings.append(
                f"{indicator}: provider may be unavailable or require credentials; skipped safely."
            )
            result.errors.append(f"{indicator}: {type(exc).__name__}: {_safe_error(exc)}")

    if frames:
        combined = pd.concat(frames, ignore_index=True)
        result.rows_inserted = len(combined)
        if write_db:
            _store_macro_data(combined)
        if write_parquet:
            result.output_paths.extend(_write_frame(combined, MACRO_DATA_DIR, f"{run_id}_macro_{provider_name}"))
        result.status = "completed_with_warnings" if result.errors or result.warnings else "completed"
    elif result.status == "running":
        result.status = "failed"
    _record_ingestion_run(result, started_at, requested)
    return result


def get_openbb_research_context(
    symbols: list[str],
    asset_classes: list[str],
    include_macro: bool = True,
) -> list[dict[str, Any]]:
    """Build lightweight research context from already-ingested local OpenBB data."""
    contexts: list[dict[str, Any]] = []
    if symbols:
        placeholders = ", ".join(["?"] * len(symbols))
        market = fetch_dataframe(
            f"""
            SELECT symbol, asset_class, provider, interval, COUNT(*) AS rows,
                   MAX(timestamp) AS latest_timestamp, MAX(retrieved_at) AS retrieved_at
            FROM openbb_market_data
            WHERE symbol IN ({placeholders})
            GROUP BY symbol, asset_class, provider, interval
            ORDER BY symbol, latest_timestamp DESC
            """,
            tuple(symbols),
        )
    else:
        market = fetch_dataframe(
            """
            SELECT symbol, asset_class, provider, interval, COUNT(*) AS rows,
                   MAX(timestamp) AS latest_timestamp, MAX(retrieved_at) AS retrieved_at
            FROM openbb_market_data
            GROUP BY symbol, asset_class, provider, interval
            ORDER BY retrieved_at DESC
            LIMIT 25
            """
        )
    if asset_classes and not market.empty:
        market = market[market["asset_class"].isin(asset_classes)]
    for _, row in market.iterrows():
        contexts.append({"context_type": "market_data_summary", **row.to_dict()})
    if include_macro:
        macro = fetch_dataframe(
            """
            SELECT indicator, provider, frequency, COUNT(*) AS rows,
                   MAX(timestamp) AS latest_timestamp, MAX(retrieved_at) AS retrieved_at
            FROM openbb_macro_data
            GROUP BY indicator, provider, frequency
            ORDER BY retrieved_at DESC
            LIMIT 25
            """
        )
        for _, row in macro.iterrows():
            contexts.append({"context_type": "macro_data_summary", **row.to_dict()})
    return contexts


def normalize_openbb_market_data(
    raw: Any,
    symbol: str,
    asset_class: str,
    provider: str,
    interval: str,
    run_id: str | None = None,
) -> pd.DataFrame:
    df = _to_dataframe(raw)
    if df.empty:
        return _empty_market_frame()
    df = _flatten_columns(df)
    timestamp_column = _first_existing_column(df, "timestamp", "date", "datetime", "time", "index")
    if timestamp_column is None:
        raise ValueError(f"No timestamp-like column found for {symbol}; skipping malformed provider output.")
    timestamp = _timestamp_series(df, timestamp_column)
    normalized = pd.DataFrame(
        {
            "id": [new_id("obm") for _ in range(len(df))],
            "symbol": symbol,
            "asset_class": asset_class,
            "provider": provider,
            "interval": interval,
            "timestamp": timestamp.astype(str),
            "open": _numeric_column(df, "open"),
            "high": _numeric_column(df, "high"),
            "low": _numeric_column(df, "low"),
            "close": _numeric_column(df, "close"),
            "volume": _numeric_column(df, "volume"),
            "adjusted_close": _optional_numeric_column(df, "adjusted_close", "adj_close", "adjclose"),
            "source": OPENBB_SOURCE,
            "retrieved_at": utc_now(),
            "metadata_json": json.dumps({"run_id": run_id, "raw_columns": list(map(str, df.columns))}),
        }
    )
    return normalized.dropna(subset=["timestamp", "close"]).reset_index(drop=True)


def normalize_openbb_macro_data(raw: Any, indicator: str, provider: str, run_id: str | None = None) -> pd.DataFrame:
    df = _to_dataframe(raw)
    if df.empty:
        return _empty_macro_frame()
    df = _flatten_columns(df)
    value_col = _first_existing_column(df, "value", "close", indicator.lower(), "realtime_value")
    if value_col is None:
        numeric = df.select_dtypes(include="number").columns
        value_col = str(numeric[0]) if len(numeric) else None
    if value_col is None:
        return _empty_macro_frame()
    timestamp = _timestamp_series(df)
    normalized = pd.DataFrame(
        {
            "id": [new_id("obmacro") for _ in range(len(df))],
            "indicator": indicator,
            "provider": provider,
            "frequency": "unknown",
            "timestamp": timestamp.astype(str),
            "value": pd.to_numeric(df[value_col], errors="coerce"),
            "source": OPENBB_SOURCE,
            "retrieved_at": utc_now(),
            "metadata_json": json.dumps({"run_id": run_id, "raw_columns": list(map(str, df.columns))}),
        }
    )
    return normalized.dropna(subset=["timestamp", "value"]).reset_index(drop=True)


def _fetch_openbb_market_data(
    *,
    symbol: str,
    asset_class: str,
    start_date: str,
    end_date: str | None,
    interval: str,
    provider: str,
) -> Any:
    obb = _openbb_client()
    candidates = [("equity", "price", "historical")]
    if asset_class.lower() == "crypto":
        candidates = [("crypto", "price", "historical"), ("currency", "price", "historical")]
    elif asset_class.lower() == "etf":
        candidates = [("etf", "price", "historical"), ("equity", "price", "historical")]
    for path in candidates:
        method = _resolve_attr_path(obb, path)
        if method is None:
            continue
        kwargs = {
            "symbol": symbol,
            "start_date": start_date,
            "interval": interval,
            "provider": provider,
        }
        if end_date:
            kwargs["end_date"] = end_date
        try:
            return method(**kwargs)
        except TypeError:
            kwargs.pop("interval", None)
            return method(**kwargs)
    raise RuntimeError(f"No compatible OpenBB market data endpoint found for asset_class={asset_class}.")


def _fetch_openbb_macro_data(indicator: str, start_date: str, end_date: str | None, provider: str) -> Any:
    obb = _openbb_client()
    candidates = [
        ("economy", "fred_series"),
        ("economy", "fred"),
        ("macro", "fred_series"),
    ]
    for path in candidates:
        method = _resolve_attr_path(obb, path)
        if method is None:
            continue
        kwargs = {"symbol": indicator, "start_date": start_date, "provider": provider}
        if end_date:
            kwargs["end_date"] = end_date
        try:
            return method(**kwargs)
        except TypeError:
            kwargs = {"series_id": indicator, "start_date": start_date, "provider": provider}
            if end_date:
                kwargs["end_date"] = end_date
            return method(**kwargs)
    raise RuntimeError("No compatible OpenBB macro endpoint found; provider may require credentials.")


def _openbb_client() -> Any:
    module = importlib.import_module("openbb")
    return getattr(module, "obb", module)


def _resolve_attr_path(root: Any, path: tuple[str, ...]) -> Any | None:
    current = root
    for name in path:
        current = getattr(current, name, None)
        if current is None:
            return None
    return current if callable(current) else None


def _store_market_data(df: pd.DataFrame) -> dict[str, Any]:
    key_columns = ["symbol", "asset_class", "provider", "interval", "timestamp"]
    if df.empty:
        return {"rows_inserted": 0, "rows_skipped_duplicate": 0, "rows_updated": 0, "dedupe_enabled": True}

    incoming = df.copy()
    before_batch_dedupe = len(incoming)
    incoming = incoming.drop_duplicates(subset=key_columns, keep="last").reset_index(drop=True)
    skipped_duplicate = before_batch_dedupe - len(incoming)
    existing_keys = _existing_market_keys(incoming)
    rows_to_insert = []
    for row in incoming.to_dict(orient="records"):
        key = tuple(str(row[column]) for column in key_columns)
        if key in existing_keys:
            skipped_duplicate += 1
            continue
        rows_to_insert.append(row)

    for row in rows_to_insert:
        insert_dict("openbb_market_data", row)
    return {
        "rows_inserted": len(rows_to_insert),
        "rows_skipped_duplicate": skipped_duplicate,
        "rows_updated": 0,
        "dedupe_enabled": True,
    }


def _existing_market_keys(df: pd.DataFrame) -> set[tuple[str, str, str, str, str]]:
    key_columns = ["symbol", "asset_class", "provider", "interval", "timestamp"]
    if df.empty:
        return set()
    symbols = sorted({str(value) for value in df["symbol"].dropna().unique()})
    providers = sorted({str(value) for value in df["provider"].dropna().unique()})
    intervals = sorted({str(value) for value in df["interval"].dropna().unique()})
    if not symbols or not providers or not intervals:
        return set()

    symbol_placeholders = ", ".join(["?"] * len(symbols))
    provider_placeholders = ", ".join(["?"] * len(providers))
    interval_placeholders = ", ".join(["?"] * len(intervals))
    try:
        existing = fetch_dataframe(
            f"""
            SELECT symbol, asset_class, provider, interval, timestamp
            FROM openbb_market_data
            WHERE symbol IN ({symbol_placeholders})
              AND provider IN ({provider_placeholders})
              AND interval IN ({interval_placeholders})
            """,
            tuple([*symbols, *providers, *intervals]),
        )
    except Exception:
        return set()
    if existing.empty:
        return set()
    return {tuple(str(row[column]) for column in key_columns) for _, row in existing.iterrows()}


def _store_macro_data(df: pd.DataFrame) -> None:
    for row in df.to_dict(orient="records"):
        insert_dict("openbb_macro_data", row)


def _record_ingestion_run(result: OpenBBIngestionResult, started_at: str, requested: dict[str, Any]) -> None:
    insert_dict(
        "openbb_ingestion_runs",
        {
            "run_id": result.run_id,
            "started_at": started_at,
            "finished_at": utc_now(),
            "status": result.status,
            "requested_assets_json": json.dumps(requested),
            "provider_summary_json": json.dumps(result.provider_summary),
            "rows_inserted": result.rows_inserted,
            "rows_failed": result.rows_failed,
            "warnings_json": json.dumps(result.warnings),
            "errors_json": json.dumps(result.errors),
        },
    )


def _write_frame(df: pd.DataFrame, directory: Path, stem: str) -> list[str]:
    directory.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    parquet_path = directory / f"{stem}.parquet"
    try:
        df.to_parquet(parquet_path, index=False)
        paths.append(str(parquet_path))
    except Exception as exc:
        csv_path = directory / f"{stem}.csv"
        df.to_csv(csv_path, index=False)
        paths.append(str(csv_path))
        logger.warning("Parquet write failed for OpenBB data; wrote CSV instead. Error type: %s", type(exc).__name__)
    return paths


def _to_dataframe(raw: Any) -> pd.DataFrame:
    if raw is None:
        return pd.DataFrame()
    if isinstance(raw, pd.DataFrame):
        return raw.copy()
    if hasattr(raw, "to_df"):
        return raw.to_df().copy()
    if hasattr(raw, "results"):
        rows = []
        for item in raw.results:
            if hasattr(item, "model_dump"):
                rows.append(item.model_dump())
            elif hasattr(item, "dict"):
                rows.append(item.dict())
            else:
                rows.append(item)
        return pd.DataFrame(rows)
    return pd.DataFrame(raw)


def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result.columns = [str(column).lower().replace(" ", "_") for column in result.columns]
    return result.reset_index() if result.index.name or not isinstance(result.index, pd.RangeIndex) else result


def _timestamp_series(df: pd.DataFrame, column: str | None = None) -> pd.Series:
    column = column or _first_existing_column(df, "timestamp", "date", "datetime", "time", "index")
    if column is None:
        raise ValueError("No timestamp-like column found.")
    return pd.to_datetime(df[column], errors="coerce").dt.tz_localize(None)


def _numeric_column(df: pd.DataFrame, name: str) -> pd.Series:
    column = _first_existing_column(df, name)
    if column is None:
        return pd.Series([None] * len(df), dtype="float64")
    return pd.to_numeric(df[column], errors="coerce")


def _optional_numeric_column(df: pd.DataFrame, *names: str) -> pd.Series:
    column = _first_existing_column(df, *names)
    if column is None:
        return pd.Series([None] * len(df), dtype="float64")
    return pd.to_numeric(df[column], errors="coerce")


def _first_existing_column(df: pd.DataFrame, *names: str) -> str | None:
    lookup = {str(column).lower(): str(column) for column in df.columns}
    for name in names:
        if name.lower() in lookup:
            return lookup[name.lower()]
    return None


def _empty_market_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
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
        ]
    )


def _empty_macro_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=["id", "indicator", "provider", "frequency", "timestamp", "value", "source", "retrieved_at", "metadata_json"]
    )


def _default_provider(asset_class: str) -> str:
    try:
        config = load_config("openbb")
    except FileNotFoundError:
        config = {}
    priority = config.get("default_provider_priority", {}).get(asset_class.lower()) or ["yfinance"]
    return str(priority[0])


def _safe_error(exc: Exception) -> str:
    text = str(exc).strip()
    if not text:
        return type(exc).__name__
    redacted = re.sub(
        r"(?i)(api[_-]?key|secret|token|password|private[_-]?key)\s*[:=]\s*['\"]?[^'\"\s,;]+",
        r"\1=<redacted>",
        text,
    )
    return redacted[:500]
