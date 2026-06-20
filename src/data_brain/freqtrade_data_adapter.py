from __future__ import annotations

import math
import shutil
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from core.database import execute_many, initialize_database
from core.logger import get_logger
from core.paths import DATA_DIR
from data_brain.csv_parquet_loader import write_table
from data_brain.data_quality_checks import validate_ohlcv


logger = get_logger(__name__)


def freqtrade_available() -> bool:
    return shutil.which("freqtrade") is not None


def normalize_pair(pair: str) -> str:
    return pair.replace("/", "_").replace(":", "_")


def generate_sample_ohlcv(pair: str, timeframe: str = "1h", candles: int = 720) -> pd.DataFrame:
    """Create deterministic research candles for first-run pipeline testing."""
    base_price = {"BTC/USDT": 65000, "ETH/USDT": 3400, "SOL/USDT": 150}.get(pair, 100)
    now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    start = now - timedelta(hours=candles)
    rows = []
    for i in range(candles):
        ts = start + timedelta(hours=i)
        trend = 1 + (i / candles) * 0.12
        wave = math.sin(i / 19) * 0.025 + math.sin(i / 53) * 0.05
        close = base_price * trend * (1 + wave)
        open_ = close * (1 + math.sin(i / 7) * 0.003)
        high = max(open_, close) * (1 + 0.004 + abs(math.sin(i / 11)) * 0.003)
        low = min(open_, close) * (1 - 0.004 - abs(math.cos(i / 13)) * 0.003)
        volume = 1000 + abs(math.sin(i / 17)) * 500 + i % 24 * 12
        rows.append(
            {
                "timestamp": ts.isoformat(),
                "open": round(open_, 8),
                "high": round(high, 8),
                "low": round(low, 8),
                "close": round(close, 8),
                "volume": round(volume, 4),
                "symbol": pair,
                "timeframe": timeframe,
                "source": "sample_freqtrade_adapter",
            }
        )
    return pd.DataFrame(rows)


def download_with_freqtrade(pairs: list[str], timeframe: str, user_data_dir: Path) -> subprocess.CompletedProcess[str]:
    """Run Freqtrade's downloader when the CLI is installed."""
    command = [
        "freqtrade",
        "download-data",
        "--userdir",
        str(user_data_dir),
        "--timeframe",
        timeframe,
        "--trading-mode",
        "spot",
    ]
    for pair in pairs:
        command.extend(["--pairs", pair])
    return subprocess.run(command, capture_output=True, text=True, check=False)


def find_freqtrade_ohlcv_files(
    pairs: list[str],
    timeframe: str,
    user_data_dir: Path | None = None,
) -> dict[str, list[Path]]:
    """Find likely Freqtrade OHLCV files for the requested pairs/timeframe."""
    root = user_data_dir or DATA_DIR / "freqtrade"
    data_root = root / "data"
    search_root = data_root if data_root.exists() else root
    candidates = [
        path
        for pattern in ("*.json", "*.json.gz", "*.feather")
        for path in search_root.rglob(pattern)
        if timeframe.lower() in path.name.lower()
    ]
    matches: dict[str, list[Path]] = {pair: [] for pair in pairs}
    for pair in pairs:
        normalized = normalize_pair(pair).lower()
        compact = pair.replace("/", "").replace(":", "").lower()
        for path in candidates:
            comparable = path.name.lower().replace("-", "_").replace("/", "_").replace(":", "_")
            if normalized in comparable or compact in comparable:
                matches[pair].append(path)
    return matches


def load_freqtrade_ohlcv_file(path: Path, pair: str, timeframe: str) -> pd.DataFrame:
    """Load common Freqtrade OHLCV export formats into the local schema."""
    suffixes = "".join(path.suffixes).lower()
    if suffixes.endswith(".feather"):
        try:
            raw = pd.read_feather(path)
        except ImportError as exc:
            raise RuntimeError(
                f"Cannot read Feather file {path}. Install pyarrow or use JSON data format."
            ) from exc
    else:
        raw_obj = pd.read_json(path, compression="infer")
        raw = _coerce_json_frame(raw_obj)
    return normalize_ohlcv_frame(raw, pair, timeframe, "freqtrade_cli_import")


def _coerce_json_frame(raw: Any) -> pd.DataFrame:
    if isinstance(raw, pd.DataFrame):
        if set(raw.columns) >= {"open", "high", "low", "close", "volume"}:
            return raw
        if len(raw.columns) >= 6:
            return raw.iloc[:, :6].copy()
    raise ValueError("Unsupported Freqtrade JSON structure. Expected OHLCV rows or columns.")


def normalize_ohlcv_frame(df: pd.DataFrame, pair: str, timeframe: str, source: str) -> pd.DataFrame:
    """Normalize a raw OHLCV frame to the local market_data schema."""
    frame = df.copy()
    lower_columns = {str(column).lower(): column for column in frame.columns}
    timestamp_column = (
        lower_columns.get("timestamp")
        or lower_columns.get("date")
        or lower_columns.get("datetime")
        or lower_columns.get("time")
        or frame.columns[0]
    )
    rename_map = {}
    for target in ["open", "high", "low", "close", "volume"]:
        if target in lower_columns:
            rename_map[lower_columns[target]] = target
    frame = frame.rename(columns=rename_map)
    if not {"open", "high", "low", "close", "volume"}.issubset(frame.columns):
        if len(frame.columns) >= 6:
            frame = frame.iloc[:, :6]
            frame.columns = ["timestamp", "open", "high", "low", "close", "volume"]
            timestamp_column = "timestamp"
        else:
            raise ValueError("OHLCV file is missing required open/high/low/close/volume columns.")
    timestamps = frame[timestamp_column]
    if pd.api.types.is_numeric_dtype(timestamps):
        max_timestamp = float(timestamps.dropna().max())
        unit = "ms" if max_timestamp > 10_000_000_000 else "s"
        parsed_timestamps = pd.to_datetime(timestamps, unit=unit, utc=True)
    else:
        parsed_timestamps = pd.to_datetime(timestamps, utc=True)
    normalized = pd.DataFrame(
        {
            "timestamp": parsed_timestamps.dt.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "open": pd.to_numeric(frame["open"], errors="coerce"),
            "high": pd.to_numeric(frame["high"], errors="coerce"),
            "low": pd.to_numeric(frame["low"], errors="coerce"),
            "close": pd.to_numeric(frame["close"], errors="coerce"),
            "volume": pd.to_numeric(frame["volume"], errors="coerce"),
            "symbol": pair,
            "timeframe": timeframe,
            "source": source,
        }
    ).dropna(subset=["timestamp", "open", "high", "low", "close", "volume"])
    return normalized


def ingest_ohlcv(df: pd.DataFrame) -> None:
    initialize_database()
    warnings = validate_ohlcv(df)
    if warnings:
        raise ValueError("; ".join(warnings))
    rows = [
        (
            row["symbol"],
            row["timeframe"],
            str(row["timestamp"]),
            float(row["open"]),
            float(row["high"]),
            float(row["low"]),
            float(row["close"]),
            float(row["volume"]),
            row.get("source", "freqtrade_adapter"),
        )
        for _, row in df.iterrows()
    ]
    execute_many(
        """
        INSERT OR REPLACE INTO market_data
        (symbol, timeframe, timestamp, open, high, low, close, volume, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    if not df.empty:
        logger.info(
            "Imported %s candles for %s %s from %s",
            len(df),
            df["symbol"].iloc[0],
            df["timeframe"].iloc[0],
            df["source"].iloc[0],
        )


def import_freqtrade_data(pairs: list[str], timeframe: str, user_data_dir: Path | None = None) -> list[Path]:
    """Import actual Freqtrade OHLCV files and fail clearly if none are found."""
    matches = find_freqtrade_ohlcv_files(pairs, timeframe, user_data_dir)
    missing = [pair for pair, paths in matches.items() if not paths]
    if missing:
        root = user_data_dir or DATA_DIR / "freqtrade"
        raise FileNotFoundError(
            "No importable Freqtrade OHLCV files found for "
            f"{missing} at timeframe {timeframe} under {root}. "
            "Use --sample for demo data, or run Freqtrade download-data with JSON/JSON.GZ/Feather output."
        )
    output_paths: list[Path] = []
    for pair, paths in matches.items():
        selected = sorted(paths)[0]
        df = load_freqtrade_ohlcv_file(selected, pair, timeframe)
        warnings = validate_ohlcv(df)
        if warnings:
            raise ValueError(f"Validation failed for {selected}: {'; '.join(warnings)}")
        ingest_ohlcv(df)
        output_path = write_table(df, DATA_DIR / "processed" / f"{normalize_pair(pair)}_{timeframe}.csv")
        logger.info(
            "Freqtrade import valid: pair=%s timeframe=%s candles=%s file=%s",
            pair,
            timeframe,
            len(df),
            selected,
        )
        output_paths.append(output_path)
    return output_paths


def prepare_crypto_data(
    pairs: list[str],
    timeframe: str = "1h",
    candles: int = 720,
    use_freqtrade_cli: bool = False,
    sample: bool = False,
) -> list[Path]:
    """Download or synthesize crypto candles and load them into the local database."""
    output_paths: list[Path] = []
    user_data_dir = DATA_DIR / "freqtrade"
    if sample and use_freqtrade_cli:
        raise ValueError("Choose either --sample or --use-freqtrade-cli, not both.")
    if use_freqtrade_cli:
        if not freqtrade_available():
            raise RuntimeError("Freqtrade CLI is not installed. Install Freqtrade or use --sample for demo data.")
        result = download_with_freqtrade(pairs, timeframe, user_data_dir)
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout)
        return import_freqtrade_data(pairs, timeframe, user_data_dir)
    if not sample:
        raise ValueError(
            "No data mode selected. Use --sample for synthetic demo data or --use-freqtrade-cli "
            "to download and import actual Freqtrade OHLCV files."
        )
    for pair in pairs:
        df = generate_sample_ohlcv(pair, timeframe=timeframe, candles=candles)
        ingest_ohlcv(df)
        logger.info(
            "Sample data generated: pair=%s timeframe=%s candles=%s source=sample_freqtrade_adapter",
            pair,
            timeframe,
            len(df),
        )
        output_paths.append(
            write_table(df, DATA_DIR / "processed" / f"{normalize_pair(pair)}_{timeframe}.csv")
        )
    return output_paths
