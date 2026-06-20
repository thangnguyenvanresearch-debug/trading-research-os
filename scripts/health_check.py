from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import _bootstrap  # noqa: F401

from core.database import fetch_dataframe, utc_now
from core.paths import REPORTS_DIR, resolve_project_path
from dashboard.control_center import (
    build_safety_checklist,
    get_latest_ai_memos,
    get_latest_daily_runs,
    get_latest_engine_statuses,
    get_latest_lean_runs,
    get_latest_qlib_exports,
    get_latest_qlib_runs,
    get_openbb_data_health,
)


def collect_health_status() -> dict[str, Any]:
    """Collect a read-only project health snapshot without running engines."""
    db = _db_health()
    openbb = get_openbb_data_health()
    statuses = get_latest_engine_statuses()
    checklist = build_safety_checklist()
    unsafe = checklist[checklist["status"] == "unsafe"] if not checklist.empty else checklist
    return {
        "db_reachable": db["reachable"],
        "db_error": db["error"],
        "engine_statuses": statuses,
        "openbb_total_rows": openbb["total_rows"],
        "openbb_rows_by_symbol": _records(openbb["rows_by_symbol"]),
        "openbb_duplicate_groups": _records(openbb["duplicates"]),
        "latest_daily_run": _first_record(get_latest_daily_runs(1)),
        "latest_ai_memo": _first_record(get_latest_ai_memos(1)),
        "latest_lean_run": _first_record(get_latest_lean_runs(1)),
        "latest_qlib_run": _first_record(get_latest_qlib_runs(1)),
        "latest_qlib_export": _first_record(get_latest_qlib_exports(1)),
        "safety_unsafe_count": int(len(unsafe)) if unsafe is not None else 0,
        "safety_checks": _records(checklist),
    }


def write_health_report(status: dict[str, Any], output_dir: str | Path | None = None) -> Path:
    root = resolve_project_path(output_dir or REPORTS_DIR / "health")
    root.mkdir(parents=True, exist_ok=True)
    timestamp = utc_now().replace(":", "").replace("+", "_")
    path = root / f"health_check_{timestamp}.md"
    lines = [
        "# Trading Research OS Health Check",
        "",
        "Read-only health report. No engines were executed and no orders were placed.",
        "",
        f"- DB reachable: {status['db_reachable']}",
        f"- OpenBB rows: {status['openbb_total_rows']}",
        f"- Latest daily run: {_format_item(status['latest_daily_run'])}",
        f"- Latest AI memo: {_format_item(status['latest_ai_memo'])}",
        f"- Latest LEAN run: {_format_item(status['latest_lean_run'])}",
        f"- Latest Qlib run: {_format_item(status['latest_qlib_run'])}",
        f"- Latest Qlib export: {_format_item(status['latest_qlib_export'])}",
        f"- Safety unsafe count: {status['safety_unsafe_count']}",
        "",
        "## Engine Statuses",
        "```json",
        json.dumps(status["engine_statuses"], indent=2, default=str),
        "```",
    ]
    if status["db_error"]:
        lines.extend(["", "## DB Error", str(status["db_error"])])
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only Trading Research OS health check.")
    parser.add_argument("--write-report", action="store_true", help="Write a markdown report under reports/health.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args(argv)

    status = collect_health_status()
    if args.write_report:
        status["report_path"] = str(write_health_report(status))

    if args.json:
        print(json.dumps(status, indent=2, default=str))
    else:
        print("Trading Research OS health check")
        print(f"db_reachable={status['db_reachable']}")
        print(f"openbb_total_rows={status['openbb_total_rows']}")
        print(f"latest_daily_run={_format_item(status['latest_daily_run'])}")
        print(f"latest_ai_memo={_format_item(status['latest_ai_memo'])}")
        print(f"latest_lean_run={_format_item(status['latest_lean_run'])}")
        print(f"latest_qlib_run={_format_item(status['latest_qlib_run'])}")
        print(f"safety_unsafe_count={status['safety_unsafe_count']}")
        if args.write_report:
            print(f"report_path={status['report_path']}")
    return 0 if status["db_reachable"] else 1


def _db_health() -> dict[str, Any]:
    try:
        fetch_dataframe("SELECT 1 AS ok")
        return {"reachable": True, "error": ""}
    except Exception as exc:
        return {"reachable": False, "error": f"{type(exc).__name__}: {exc}"}


def _records(df: Any) -> list[dict[str, Any]]:
    if df is None or getattr(df, "empty", True):
        return []
    return df.to_dict(orient="records")


def _first_record(df: Any) -> dict[str, Any]:
    records = _records(df)
    return records[0] if records else {}


def _format_item(item: dict[str, Any]) -> str:
    if not item:
        return "none"
    identifier = item.get("item_id") or item.get("run_id") or item.get("export_id") or item.get("memo_id") or "unknown"
    status = item.get("status", "unknown")
    return f"{identifier} ({status})"


if __name__ == "__main__":
    raise SystemExit(main())
