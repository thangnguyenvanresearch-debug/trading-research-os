from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from core.database import fetch_dataframe, utc_now
from core.paths import DATA_DIR, resolve_project_path


LEAN_DATA_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]


def load_openbb_for_lean(
    symbols: list[str],
    provider: str = "yfinance",
    interval: str = "1d",
) -> pd.DataFrame:
    """Load local OpenBB OHLCV rows for LEAN research export. No external fetch is performed."""
    if not symbols:
        return _empty_lean_frame()
    placeholders = ", ".join(["?"] * len(symbols))
    try:
        rows = fetch_dataframe(
            f"""
            SELECT symbol, asset_class, provider, interval, timestamp, open, high, low, close, volume
            FROM openbb_market_data
            WHERE symbol IN ({placeholders}) AND provider = ? AND interval = ?
            ORDER BY symbol, timestamp
            """,
            tuple([*symbols, provider, interval]),
        )
    except Exception as exc:
        if _is_missing_table_error(exc):
            return _empty_lean_frame()
        raise
    if rows.empty:
        return _empty_lean_frame()
    rows = rows.drop_duplicates(
        subset=["symbol", "asset_class", "provider", "interval", "timestamp"],
        keep="last",
    )
    rows["timestamp"] = pd.to_datetime(rows["timestamp"], errors="coerce")
    rows = rows.dropna(subset=["timestamp", "close"]).sort_values(["symbol", "timestamp"]).reset_index(drop=True)
    return rows


def export_lean_research_data(
    symbols: list[str],
    provider: str = "yfinance",
    interval: str = "1d",
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Export local OpenBB data into simple LEAN research bridge CSV files."""
    root = resolve_project_path(output_dir or (DATA_DIR / "generated" / "lean" / "data"))
    root.mkdir(parents=True, exist_ok=True)
    data = load_openbb_for_lean(symbols, provider, interval)
    manifest: dict[str, Any] = {
        "label": "LEAN research bridge data",
        "provider": provider,
        "interval": interval,
        "created_at": utc_now(),
        "symbols": {},
        "warnings": [],
    }
    paths: dict[str, str] = {}
    for symbol in symbols:
        frame = data[data["symbol"] == symbol].copy() if not data.empty else pd.DataFrame(columns=LEAN_DATA_COLUMNS)
        path = root / f"{symbol}_{provider}_{interval}.csv".replace("/", "_")
        export_frame = frame[LEAN_DATA_COLUMNS].copy() if not frame.empty else pd.DataFrame(columns=LEAN_DATA_COLUMNS)
        if not export_frame.empty:
            export_frame["timestamp"] = pd.to_datetime(export_frame["timestamp"]).dt.strftime("%Y-%m-%d")
        export_frame.to_csv(path, index=False)
        paths[symbol] = str(path)
        manifest["symbols"][symbol] = {"path": str(path), "rows": int(len(export_frame))}
        if export_frame.empty:
            manifest["warnings"].append(f"No local OpenBB rows exported for {symbol}.")
    manifest_path = root / "data_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    return {
        "dataframe": data,
        "paths": paths,
        "manifest_path": str(manifest_path),
        "row_counts": {symbol: int(manifest["symbols"][symbol]["rows"]) for symbol in symbols},
        "warnings": manifest["warnings"],
    }


def _empty_lean_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=["symbol", "asset_class", "provider", "interval", *LEAN_DATA_COLUMNS])


def _is_missing_table_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "openbb_market_data" in message and (
        "no such table" in message or "does not exist" in message or "not found" in message or "catalog error" in message
    )
