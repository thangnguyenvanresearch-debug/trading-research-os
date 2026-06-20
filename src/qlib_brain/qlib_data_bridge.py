from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from core.config_loader import load_config
from core.database import fetch_dataframe, insert_dict, new_id, utc_now
from core.paths import DATA_DIR, resolve_project_path


QLIB_FEATURE_COLUMNS = [
    "timestamp",
    "symbol",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_return_1d",
    "close_return_5d",
    "momentum_20d",
    "volatility_20d",
    "volume_zscore_20d",
    "label_forward_return_5d",
]


def load_openbb_for_qlib(
    symbols: list[str],
    provider: str = "yfinance",
    interval: str = "1d",
) -> pd.DataFrame:
    """Load local OpenBB rows for Qlib-style research export. No external fetch is performed."""
    if not symbols:
        return _empty_ohlcv_frame()
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
            return _empty_ohlcv_frame()
        raise
    if rows.empty:
        return _empty_ohlcv_frame()
    rows = rows.drop_duplicates(
        subset=["symbol", "asset_class", "provider", "interval", "timestamp"],
        keep="last",
    )
    rows["timestamp"] = pd.to_datetime(rows["timestamp"], errors="coerce")
    for column in ["open", "high", "low", "close", "volume"]:
        rows[column] = pd.to_numeric(rows[column], errors="coerce")
    rows = rows.dropna(subset=["symbol", "timestamp", "close"])
    return rows.sort_values(["symbol", "timestamp"]).reset_index(drop=True)


def build_qlib_research_features(df: pd.DataFrame, horizon_days: int = 5) -> pd.DataFrame:
    """Build simple trailing features and a clearly separated future-return label."""
    if df.empty:
        return pd.DataFrame(columns=QLIB_FEATURE_COLUMNS)
    horizon = max(int(horizon_days), 1)
    frames: list[pd.DataFrame] = []
    for symbol, group in df.sort_values(["symbol", "timestamp"]).groupby("symbol", sort=False):
        frame = group.copy().reset_index(drop=True)
        close = pd.to_numeric(frame["close"], errors="coerce")
        volume = pd.to_numeric(frame["volume"], errors="coerce")
        frame["close_return_1d"] = close.pct_change(1)
        frame["close_return_5d"] = close.pct_change(5)
        frame["momentum_20d"] = close.pct_change(20)
        frame["volatility_20d"] = frame["close_return_1d"].rolling(20, min_periods=5).std()
        volume_mean = volume.rolling(20, min_periods=5).mean()
        volume_std = volume.rolling(20, min_periods=5).std()
        frame["volume_zscore_20d"] = (volume - volume_mean) / volume_std.replace(0, pd.NA)
        frame["label_forward_return_5d"] = close.shift(-horizon) / close - 1
        frame["symbol"] = symbol
        frames.append(frame[QLIB_FEATURE_COLUMNS])
    features = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=QLIB_FEATURE_COLUMNS)
    return features.dropna(subset=["label_forward_return_5d"]).reset_index(drop=True)


def export_qlib_dataset(
    symbols: list[str],
    provider: str = "yfinance",
    interval: str = "1d",
    horizon_days: int = 5,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Export a local Qlib-style research feature dataset and record it in the database."""
    export_id = new_id("qlib_export")
    created_at = utc_now()
    warnings: list[str] = []
    errors: list[str] = []
    root = resolve_project_path(output_dir or _default_output_dir()) / "datasets" / export_id
    root.mkdir(parents=True, exist_ok=True)
    raw = load_openbb_for_qlib(symbols, provider, interval)
    if raw.empty:
        warnings.append("No local OpenBB rows found for Qlib export.")
    features = build_qlib_research_features(raw, horizon_days=horizon_days)
    if features.empty:
        warnings.append("Qlib feature dataset is empty after feature/label construction.")
    features_path = root / "features.csv"
    features.to_csv(features_path, index=False)
    per_symbol_paths: dict[str, str] = {}
    for symbol in symbols:
        symbol_frame = features[features["symbol"] == symbol] if not features.empty else pd.DataFrame(columns=QLIB_FEATURE_COLUMNS)
        path = root / f"{symbol}_features.csv".replace("/", "_")
        symbol_frame.to_csv(path, index=False)
        per_symbol_paths[symbol] = str(path)
    manifest = {
        "label": "Qlib research-only local OpenBB feature dataset",
        "export_id": export_id,
        "created_at": created_at,
        "symbols": symbols,
        "provider": provider,
        "interval": interval,
        "horizon_days": horizon_days,
        "feature_columns": [column for column in QLIB_FEATURE_COLUMNS if column not in {"timestamp", "symbol", "label_forward_return_5d"}],
        "label_column": "label_forward_return_5d",
        "lookahead_note": "Future return is stored only as label; all features use current/trailing data.",
        "rows": int(len(features)),
        "per_symbol_paths": per_symbol_paths,
        "warnings": warnings,
    }
    manifest_path = root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
    status = "exported_with_warnings" if warnings else "exported"
    _record_dataset_export(
        export_id=export_id,
        created_at=created_at,
        status=status,
        symbols=symbols,
        provider=provider,
        interval=interval,
        features=features,
        features_path=features_path,
        manifest_path=manifest_path,
        warnings=warnings,
        errors=errors,
        metadata={"horizon_days": horizon_days, "raw_rows": int(len(raw))},
    )
    return {
        "export_id": export_id,
        "status": status,
        "dataframe": features,
        "row_count": int(len(features)),
        "feature_count": len(QLIB_FEATURE_COLUMNS) - 3,
        "output_path": str(features_path),
        "manifest_path": str(manifest_path),
        "warnings": warnings,
        "errors": errors,
    }


def _record_dataset_export(
    *,
    export_id: str,
    created_at: str,
    status: str,
    symbols: list[str],
    provider: str,
    interval: str,
    features: pd.DataFrame,
    features_path: Path,
    manifest_path: Path,
    warnings: list[str],
    errors: list[str],
    metadata: dict[str, Any],
) -> None:
    insert_dict(
        "qlib_dataset_exports",
        {
            "export_id": export_id,
            "created_at": created_at,
            "status": status,
            "symbols": json.dumps(symbols),
            "provider": provider,
            "interval": interval,
            "feature_count": len(QLIB_FEATURE_COLUMNS) - 3,
            "row_count": int(len(features)),
            "output_path": str(features_path),
            "manifest_path": str(manifest_path),
            "warnings_json": json.dumps(warnings),
            "errors_json": json.dumps(errors),
            "metadata_json": json.dumps(metadata),
        },
    )


def _default_output_dir() -> Path:
    try:
        config = load_config("qlib")
        return resolve_project_path(config.get("output_dir", DATA_DIR / "generated" / "qlib"))
    except FileNotFoundError:
        return DATA_DIR / "generated" / "qlib"


def _empty_ohlcv_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=["symbol", "asset_class", "provider", "interval", "timestamp", "open", "high", "low", "close", "volume"])


def _is_missing_table_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "openbb_market_data" in message and (
        "no such table" in message or "does not exist" in message or "not found" in message or "catalog error" in message
    )
