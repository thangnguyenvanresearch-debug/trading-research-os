from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from core.config_loader import load_config
from core.database import fetch_dataframe, insert_dict, new_id, utc_now
from core.paths import REPORTS_DIR, resolve_project_path
from lean_brain.lean_adapter import assert_lean_research_only, get_lean_status
from lean_brain.lean_data_bridge import export_lean_research_data
from lean_brain.lean_project_builder import create_lean_research_project


def run_lean_backtest(
    symbols: list[str],
    provider: str = "yfinance",
    interval: str = "1d",
    strategy_name: str = "equal_weight_demo",
    cash: float = 100000,
    skip_run: bool = False,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create local LEAN research artifacts and optionally attempt a local LEAN CLI backtest."""
    active = _lean_config(config)
    assert_lean_research_only(active)
    run_id = new_id("lean_bt")
    created_at = utc_now()
    warnings: list[str] = []
    errors: list[str] = []
    reports_dir = resolve_project_path(active.get("reports_dir", REPORTS_DIR / "lean"))
    reports_dir.mkdir(parents=True, exist_ok=True)

    data_export = export_lean_research_data(
        symbols=symbols,
        provider=provider,
        interval=interval,
        output_dir=resolve_project_path(active.get("output_dir", "data/generated/lean")) / "data",
    )
    warnings.extend(data_export.get("warnings", []))
    project = create_lean_research_project(
        strategy_name=strategy_name,
        symbols=symbols,
        output_dir=resolve_project_path(active.get("output_dir", "data/generated/lean")) / "projects",
        cash=cash,
        benchmark=str(active.get("benchmark", "SPY")),
        data_manifest_path=data_export.get("manifest_path"),
    )
    status = get_lean_status(active)
    command: list[str] = []
    metrics: dict[str, Any] = {}
    stdout = ""
    stderr = ""

    if skip_run:
        run_status = "skeleton_created"
        warnings.append("LEAN run skipped by request; research-only skeleton was created.")
    elif not status["lean_cli_available"]:
        run_status = "unavailable"
        warnings.extend(status.get("warnings", []))
    else:
        command = [
            str(status.get("lean_cli_path") or "lean"),
            "backtest",
            str(project["project_path"]),
            "--lean-config",
            str(Path(project["project_path"]) / "lean.json"),
        ]
        try:
            completed = subprocess.run(
                command,
                cwd=str(resolve_project_path(project["project_path"])),
                capture_output=True,
                text=True,
                timeout=900,
                check=False,
            )
            stdout = _safe_text(completed.stdout)
            stderr = _safe_text(completed.stderr)
            if completed.returncode == 0:
                metrics_result = parse_lean_results(project["project_path"])
                metrics = metrics_result["metrics"]
                warnings.extend(metrics_result["warnings"])
                run_status = "completed"
            else:
                run_status = "failed"
                errors.append(f"LEAN CLI exited with code {completed.returncode}.")
                if stderr:
                    errors.append(stderr[:1000])
        except Exception as exc:
            run_status = "failed"
            errors.append(f"{type(exc).__name__}: {_safe_text(str(exc))}")

    report_path = _write_lean_report(
        run_id=run_id,
        status=run_status,
        symbols=symbols,
        strategy_name=strategy_name,
        project_path=str(project["project_path"]),
        data_export=data_export,
        metrics=metrics,
        warnings=warnings,
        errors=errors,
        stdout=stdout,
        stderr=stderr,
        reports_dir=reports_dir,
    )
    _record_lean_run(
        run_id=run_id,
        created_at=created_at,
        status=run_status,
        symbols=symbols,
        strategy_name=strategy_name,
        engine_status=status,
        command_text=" ".join(command),
        project_path=str(project["project_path"]),
        report_path=str(report_path),
        metrics=metrics,
        warnings=warnings,
        errors=errors,
        metadata={
            "data_export": {key: value for key, value in data_export.items() if key != "dataframe"},
            "skip_run": skip_run,
            "cash": cash,
        },
    )
    _record_lean_metrics(run_id, metrics)
    return {
        "run_id": run_id,
        "status": run_status,
        "project_path": str(project["project_path"]),
        "report_path": str(report_path),
        "data_paths": data_export["paths"],
        "manifest_path": data_export["manifest_path"],
        "metrics": metrics,
        "warnings": warnings,
        "errors": errors,
        "lean_status": status,
    }


def parse_lean_results(project_path: str | Path) -> dict[str, Any]:
    """Best-effort parser for local LEAN statistics files. It does not invent missing metrics."""
    root = resolve_project_path(project_path)
    candidates = list(root.rglob("*.json")) if root.exists() else []
    metrics: dict[str, Any] = {}
    warnings: list[str] = []
    for path in candidates:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        stats = payload.get("Statistics") or payload.get("statistics") or payload.get("TotalPerformance") or {}
        if isinstance(stats, dict):
            for key, value in stats.items():
                parsed = _parse_metric(value)
                metrics[str(key)] = parsed
    if not metrics:
        warnings.append("No LEAN result/statistics JSON metrics found.")
    return {"metrics": metrics, "warnings": warnings}


def _record_lean_run(
    *,
    run_id: str,
    created_at: str,
    status: str,
    symbols: list[str],
    strategy_name: str,
    engine_status: dict[str, Any],
    command_text: str,
    project_path: str,
    report_path: str,
    metrics: dict[str, Any],
    warnings: list[str],
    errors: list[str],
    metadata: dict[str, Any],
) -> None:
    insert_dict(
        "lean_backtest_runs",
        {
            "run_id": run_id,
            "created_at": created_at,
            "finished_at": utc_now(),
            "status": status,
            "symbols": json.dumps(symbols),
            "strategy_name": strategy_name,
            "engine_status": json.dumps(engine_status),
            "command_text": command_text,
            "project_path": project_path,
            "report_path": report_path,
            "metrics_json": json.dumps(metrics, default=str),
            "warnings_json": json.dumps(warnings),
            "errors_json": json.dumps(errors),
            "metadata_json": json.dumps(metadata, default=str),
        },
    )


def _record_lean_metrics(run_id: str, metrics: dict[str, Any]) -> None:
    for name, value in metrics.items():
        metric_value = value if isinstance(value, (int, float)) else None
        insert_dict(
            "lean_backtest_metrics",
            {
                "metric_id": new_id("lean_metric"),
                "run_id": run_id,
                "symbol": None,
                "metric_name": str(name),
                "metric_value": metric_value,
                "metric_text": None if metric_value is not None else str(value),
                "created_at": utc_now(),
            },
        )


def _write_lean_report(
    *,
    run_id: str,
    status: str,
    symbols: list[str],
    strategy_name: str,
    project_path: str,
    data_export: dict[str, Any],
    metrics: dict[str, Any],
    warnings: list[str],
    errors: list[str],
    stdout: str,
    stderr: str,
    reports_dir: Path,
) -> Path:
    path = reports_dir / f"{run_id}_{strategy_name}.md"
    body = [
        f"# LEAN Research Backtest: {run_id}",
        "",
        f"- Status: {status}",
        f"- Strategy: {strategy_name}",
        f"- Symbols: {', '.join(symbols)}",
        f"- Project path: {project_path}",
        "- Mode: research-only local backtest/skeleton.",
        "- No live trading, brokerage credentials, QuantConnect cloud login, futures, leverage, or real orders.",
        "",
        "## Local Data Export",
        "",
        "```json",
        json.dumps({key: value for key, value in data_export.items() if key != "dataframe"}, indent=2, default=str),
        "```",
        "",
        "## Metrics",
        "",
        "```json",
        json.dumps(metrics, indent=2, default=str),
        "```",
        "",
        "## Warnings",
        "",
        "```json",
        json.dumps(warnings, indent=2),
        "```",
        "",
        "## Errors",
        "",
        "```json",
        json.dumps(errors, indent=2),
        "```",
    ]
    if stdout or stderr:
        body.extend(["", "## CLI Output", "", "```text", stdout, stderr, "```"])
    path.write_text("\n".join(body), encoding="utf-8")
    return path


def _lean_config(config: dict[str, Any] | None) -> dict[str, Any]:
    active = load_config("lean")
    if config:
        active.update(config)
    return active


def _parse_metric(value: Any) -> Any:
    if isinstance(value, (int, float)):
        return value
    text = str(value).replace("%", "").replace("$", "").replace(",", "").strip()
    try:
        return float(text)
    except ValueError:
        return value


def _safe_text(value: str) -> str:
    return value.replace("\x00", "")[:5000]
