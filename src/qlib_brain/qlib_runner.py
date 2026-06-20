from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from core.config_loader import load_config
from core.database import fetch_dataframe, insert_dict, new_id, utc_now
from core.paths import REPORTS_DIR, resolve_project_path
from qlib_brain.qlib_adapter import assert_qlib_research_only, get_qlib_status
from qlib_brain.qlib_data_bridge import export_qlib_dataset


def run_qlib_experiment(
    symbols: list[str],
    provider: str = "yfinance",
    interval: str = "1d",
    experiment_name: str = "qlib_demo",
    horizon_days: int = 5,
    skip_run: bool = False,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Export local factor data and optionally attempt a Qlib research experiment."""
    active = _qlib_config(config)
    assert_qlib_research_only(active)
    run_id = new_id("qlib_run")
    created_at = utc_now()
    reports_dir = resolve_project_path(active.get("reports_dir", REPORTS_DIR / "qlib"))
    reports_dir.mkdir(parents=True, exist_ok=True)
    dataset = export_qlib_dataset(
        symbols=symbols,
        provider=provider,
        interval=interval,
        horizon_days=horizon_days,
        output_dir=resolve_project_path(active.get("output_dir", "data/generated/qlib")),
    )
    status = get_qlib_status(active)
    warnings = list(dataset.get("warnings", []))
    errors = list(dataset.get("errors", []))
    metrics: dict[str, Any] = {}
    predictions: list[dict[str, Any]] = []

    if skip_run:
        run_status = "dataset_exported"
        warnings.append("Qlib run skipped by request; dataset export only.")
    elif not status["qlib_import_available"]:
        run_status = "unavailable"
        warnings.extend(status.get("warnings", []))
    else:
        baseline = fallback_baseline_experiment(dataset["dataframe"], experiment_name=experiment_name)
        metrics = baseline["metrics"]
        predictions = baseline["predictions"]
        warnings.append("Qlib package is importable; ran local pandas baseline only. Full Qlib trainer is future work.")
        run_status = "completed_with_warnings"

    report_path = _write_qlib_report(
        run_id=run_id,
        status=run_status,
        symbols=symbols,
        experiment_name=experiment_name,
        dataset=dataset,
        qlib_status=status,
        metrics=metrics,
        predictions=predictions,
        warnings=warnings,
        errors=errors,
        reports_dir=reports_dir,
    )
    _record_experiment_run(
        run_id=run_id,
        created_at=created_at,
        status=run_status,
        symbols=symbols,
        experiment_name=experiment_name,
        qlib_available=bool(status["qlib_import_available"]),
        dataset_export_id=dataset["export_id"],
        report_path=str(report_path),
        metrics=metrics,
        warnings=warnings,
        errors=errors,
        metadata={
            "provider": provider,
            "interval": interval,
            "horizon_days": horizon_days,
            "dataset_output_path": dataset["output_path"],
            "dataset_manifest_path": dataset["manifest_path"],
            "skip_run": skip_run,
            "qlib_status": status,
        },
    )
    if predictions and status["qlib_import_available"]:
        _record_predictions(run_id, predictions)
    return {
        "run_id": run_id,
        "status": run_status,
        "dataset_export_id": dataset["export_id"],
        "features_path": dataset["output_path"],
        "manifest_path": dataset["manifest_path"],
        "report_path": str(report_path),
        "metrics": metrics,
        "predictions_count": len(predictions) if status["qlib_import_available"] else 0,
        "warnings": warnings,
        "errors": errors,
        "qlib_status": status,
    }


def fallback_baseline_experiment(features: pd.DataFrame, experiment_name: str = "qlib_demo") -> dict[str, Any]:
    """Compute a small local research baseline. This is not a trading signal."""
    if features.empty:
        return {"metrics": {}, "predictions": []}
    latest = features.sort_values(["symbol", "timestamp"]).groupby("symbol", as_index=False).tail(1)
    latest = latest.copy()
    latest["score"] = latest["momentum_20d"].fillna(0) - latest["volatility_20d"].fillna(0)
    predictions = [
        {
            "symbol": str(row["symbol"]),
            "timestamp": str(row["timestamp"]),
            "score": float(row["score"]) if pd.notna(row["score"]) else None,
            "label": float(row["label_forward_return_5d"]) if pd.notna(row["label_forward_return_5d"]) else None,
            "model_name": f"{experiment_name}_pandas_baseline_research_only",
        }
        for _, row in latest.iterrows()
    ]
    metrics = {
        "baseline_rows": int(len(features)),
        "symbols_ranked": int(latest["symbol"].nunique()),
        "mean_label_forward_return_5d": float(features["label_forward_return_5d"].mean()),
    }
    return {"metrics": metrics, "predictions": predictions}


def _record_experiment_run(
    *,
    run_id: str,
    created_at: str,
    status: str,
    symbols: list[str],
    experiment_name: str,
    qlib_available: bool,
    dataset_export_id: str,
    report_path: str,
    metrics: dict[str, Any],
    warnings: list[str],
    errors: list[str],
    metadata: dict[str, Any],
) -> None:
    insert_dict(
        "qlib_experiment_runs",
        {
            "run_id": run_id,
            "created_at": created_at,
            "finished_at": utc_now(),
            "status": status,
            "symbols": json.dumps(symbols),
            "experiment_name": experiment_name,
            "qlib_available": int(qlib_available),
            "dataset_export_id": dataset_export_id,
            "report_path": report_path,
            "metrics_json": json.dumps(metrics, default=str),
            "warnings_json": json.dumps(warnings),
            "errors_json": json.dumps(errors),
            "metadata_json": json.dumps(metadata, default=str),
        },
    )


def _record_predictions(run_id: str, predictions: list[dict[str, Any]]) -> None:
    for prediction in predictions:
        insert_dict(
            "qlib_predictions",
            {
                "prediction_id": new_id("qlib_pred"),
                "run_id": run_id,
                "symbol": prediction.get("symbol"),
                "timestamp": prediction.get("timestamp"),
                "score": prediction.get("score"),
                "label": prediction.get("label"),
                "model_name": prediction.get("model_name"),
                "created_at": utc_now(),
                "metadata_json": json.dumps({"research_only": True}),
            },
        )


def _write_qlib_report(
    *,
    run_id: str,
    status: str,
    symbols: list[str],
    experiment_name: str,
    dataset: dict[str, Any],
    qlib_status: dict[str, Any],
    metrics: dict[str, Any],
    predictions: list[dict[str, Any]],
    warnings: list[str],
    errors: list[str],
    reports_dir: Path,
) -> Path:
    path = reports_dir / f"{run_id}_{experiment_name}.md"
    body = [
        f"# Qlib Research Experiment: {run_id}",
        "",
        f"- Status: {status}",
        f"- Experiment: {experiment_name}",
        f"- Symbols: {', '.join(symbols)}",
        f"- Dataset export: {dataset['export_id']}",
        f"- Features path: {dataset['output_path']}",
        f"- Manifest path: {dataset['manifest_path']}",
        "- Mode: research-only ML/factor analysis.",
        "- No cloud credentials, brokerage credentials, live trading, futures, leverage, or real orders.",
        "- Scores are research artifacts, not trading advice.",
        "",
        "## Qlib Status",
        "```json",
        json.dumps(qlib_status, indent=2, default=str),
        "```",
        "",
        "## Metrics",
        "```json",
        json.dumps(metrics, indent=2, default=str),
        "```",
        "",
        "## Prediction Preview",
        "```json",
        json.dumps(predictions[:10], indent=2, default=str),
        "```",
        "",
        "## Warnings",
        "```json",
        json.dumps(warnings, indent=2),
        "```",
        "",
        "## Errors",
        "```json",
        json.dumps(errors, indent=2),
        "```",
    ]
    path.write_text("\n".join(body), encoding="utf-8")
    return path


def _qlib_config(config: dict[str, Any] | None) -> dict[str, Any]:
    active = load_config("qlib")
    if config:
        active.update(config)
    return active
