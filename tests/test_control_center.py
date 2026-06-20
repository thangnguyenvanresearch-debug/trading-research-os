from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import core.database as database
from core.database import initialize_database, insert_dict
from dashboard import control_center
from dashboard.control_center import (
    build_next_actions,
    build_safety_checklist,
    get_latest_engine_statuses,
    get_openbb_data_health,
    load_engine_registry,
    summarize_text,
    write_control_center_report,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def test_control_center_helpers_handle_missing_tables(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "missing.sqlite")
    health = get_openbb_data_health()

    assert health["total_rows"] == 0
    assert health["rows_by_symbol"].empty


def test_engine_registry_loads() -> None:
    registry = load_engine_registry()

    assert not registry.empty
    assert {"engine", "status", "safe_for_live", "execution_allowed"}.issubset(registry.columns)
    assert "qlib" in set(registry["engine"])


def test_safety_checklist_contains_mandatory_disabled_items() -> None:
    checklist = build_safety_checklist()

    required = {
        "OpenAI API disabled",
        "ChatGPT OAuth disabled",
        "credentials disabled",
        "brokerage disabled",
        "live trading disabled",
        "futures disabled",
        "leverage disabled",
        "real orders disabled",
        "Qlib daily disabled by default",
        "LEAN daily disabled by default",
    }
    assert required.issubset(set(checklist["check"]))
    assert not (checklist["status"] == "unsafe").any()


def test_next_actions_flag_unavailable_engines(monkeypatch) -> None:
    monkeypatch.setattr(
        control_center,
        "get_qlib_status",
        lambda: {"qlib_import_available": False, "status": "missing"},
    )
    monkeypatch.setattr(
        control_center,
        "get_lean_status",
        lambda: {"lean_cli_available": True, "status": "partial"},
    )
    monkeypatch.setattr(
        control_center,
        "get_local_ai_status",
        lambda config=None: {"available": False, "model": "qwen2.5:3b"},
    )

    actions = build_next_actions()

    assert any("Qlib installed execution not verified" in action for action in actions)
    assert any("Start Ollama" in action or "Local AI unavailable" in action for action in actions)


def test_latest_engine_statuses_are_structured(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    initialize_database()
    insert_dict(
        "openbb_market_data",
        {
            "id": "obm_test",
            "symbol": "AAPL",
            "asset_class": "equity",
            "provider": "yfinance",
            "interval": "1d",
            "timestamp": "2024-01-01",
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
    monkeypatch.setattr(control_center, "get_local_ai_status", lambda config=None: {"available": False, "model": "x"})

    statuses = get_latest_engine_statuses()

    assert statuses["openbb"]["rows"] == 1
    assert statuses["latest_daily_run"]["scheduler_state"] == "not_verified"
    assert statuses["qlib"]["safe_for_live"] is False
    assert statuses["lean"]["safe_for_live"] is False
    assert "cli_detected" in statuses["lean"]


def test_lean_timeout_is_not_labeled_ready(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    initialize_database()
    insert_dict(
        "lean_backtest_runs",
        {
            "run_id": "lean_timeout",
            "created_at": "2026-06-20T01:00:00+00:00",
            "finished_at": "2026-06-20T01:15:00+00:00",
            "status": "failed",
            "symbols": '["AAPL", "MSFT"]',
            "strategy_name": "equal_weight_demo",
            "engine_status": "ready",
            "command_text": "lean backtest equal_weight_demo --lean-config local",
            "project_path": "data/generated/lean/projects/test",
            "report_path": "reports/lean/test.md",
            "metrics_json": "{}",
            "warnings_json": "[]",
            "errors_json": '["Timed out after 900 seconds"]',
            "metadata_json": "{}",
        },
    )
    monkeypatch.setattr(
        control_center,
        "get_lean_status",
        lambda: {"lean_cli_available": True, "status": "ready", "safe_for_live": False},
    )
    monkeypatch.setattr(control_center, "get_local_ai_status", lambda config=None: {"available": False, "model": "x"})

    statuses = get_latest_engine_statuses()

    assert statuses["lean"]["status"] == "executable_failed_timeout"
    assert statuses["lean"]["status"] != "ready"
    assert statuses["lean"]["cli_detected"] is True
    assert statuses["lean"]["skeleton_available"] is True
    assert statuses["lean"]["executable_verified"] is False
    assert statuses["lean"]["latest_executable_status"] == "failed"


def test_daily_status_is_latest_db_run_not_scheduler_state(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    initialize_database()
    insert_dict(
        "daily_research_runs",
        {
            "run_id": "daily_test",
            "started_at": "2026-06-20T08:30:00+00:00",
            "finished_at": "2026-06-20T08:35:00+00:00",
            "status": "completed_with_warnings",
            "symbols": '["AAPL", "MSFT"]',
            "provider": "yfinance",
            "interval": "1d",
            "task_type": "daily_research_note",
            "openbb_ingestion_run_id": "openbb_test",
            "analytics_report_path": "reports/daily_research/test.md",
            "local_ai_memo_id": "memo_test",
            "local_ai_report_path": "reports/local_ai/test.md",
            "warnings_json": "[]",
            "errors_json": "[]",
            "metadata_json": "{}",
        },
    )
    monkeypatch.setattr(control_center, "get_local_ai_status", lambda config=None: {"available": False, "model": "x"})

    statuses = get_latest_engine_statuses()

    assert "latest_daily_run" in statuses
    assert "daily_scheduler" not in statuses
    assert statuses["latest_daily_run"]["status"] == "completed_with_warnings"
    assert statuses["latest_daily_run"]["scheduler_state"] == "not_verified"
    assert statuses["latest_daily_run"]["source"] == "daily_research_runs"


def test_warning_error_summarizer_truncates_safely() -> None:
    long_payload = {"errors": ["x" * 500], "note": "kept compact"}

    summary = summarize_text(long_payload, limit=80)

    assert len(summary) <= 80
    assert summary.endswith("...")
    assert "errors" in summary


def test_dashboard_page_compiles() -> None:
    page = PROJECT_ROOT / "src" / "dashboard" / "pages" / "00_research_control_center.py"

    compile(page.read_text(encoding="utf-8"), str(page), "exec")


def test_cli_report_writes_markdown(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    initialize_database()

    result = write_control_center_report(output_dir=tmp_path / "reports")

    path = Path(result["report_path"])
    assert path.exists()
    assert "Research Control Center Status" in path.read_text(encoding="utf-8")


def test_report_control_center_cli_parser_imports() -> None:
    spec = importlib.util.spec_from_file_location(
        "report_control_center_status_cli",
        SCRIPTS_DIR / "report_control_center_status.py",
    )
    cli = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(cli)
    assert cli.main


def test_control_center_runtime_has_no_live_order_or_credential_surface() -> None:
    source = control_center.__loader__.get_source(control_center.__name__).lower()
    for forbidden in ["openai_api_key", "create_order", "place_order", "market_order", "limit_order", "buy_order", "sell_order"]:
        assert forbidden not in source
