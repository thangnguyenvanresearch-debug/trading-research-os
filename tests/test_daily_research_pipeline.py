from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import core.database as database
from core.database import fetch_dataframe, initialize_database, insert_dict
from pipeline import daily_research_pipeline
from pipeline.daily_research_pipeline import run_daily_research_pipeline


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

spec = importlib.util.spec_from_file_location("run_daily_research_cli", SCRIPTS_DIR / "run_daily_research.py")
run_daily_research_cli = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(run_daily_research_cli)


def test_dry_run_works_without_fetching_external_data(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    monkeypatch.setattr(daily_research_pipeline, "REPORTS_DIR", tmp_path / "reports")
    initialize_database()
    called = {"ingest": False, "ai": False}
    monkeypatch.setattr(
        daily_research_pipeline,
        "ingest_openbb_market_data",
        lambda **kwargs: called.update(ingest=True),
    )
    monkeypatch.setattr(
        daily_research_pipeline,
        "run_local_ai_research",
        lambda **kwargs: called.update(ai=True),
    )

    result = run_daily_research_pipeline(symbols=["AAPL"], dry_run=True)

    assert result.status == "dry_run"
    assert called == {"ingest": False, "ai": False}
    stored = fetch_dataframe("SELECT run_id, status FROM daily_research_runs")
    assert stored.iloc[0]["status"] == "dry_run"


def test_environment_diagnostics_are_included_in_metadata(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    monkeypatch.setattr(daily_research_pipeline, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(daily_research_pipeline, "_ollama_available", lambda: True)
    initialize_database()

    result = run_daily_research_pipeline(symbols=["AAPL"], dry_run=True, model="qwen2.5:3b")

    stored = fetch_dataframe("SELECT metadata_json FROM daily_research_runs WHERE run_id = ?", (result.run_id,))
    metadata = stored.iloc[0]["metadata_json"]
    assert "python_executable" in metadata
    assert "python_version" in metadata
    assert "openbb_installed" in metadata
    assert "ollama_available" in metadata
    assert "model_requested" in metadata
    assert "fresh_openbb_ingestion_attempted" in metadata
    assert "existing_openbb_rows_used" in metadata


def test_skip_ingest_uses_existing_local_data(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    monkeypatch.setattr(daily_research_pipeline, "REPORTS_DIR", tmp_path / "reports")
    initialize_database()
    _insert_openbb_row("AAPL", "2024-01-01", 100)
    monkeypatch.setattr(
        daily_research_pipeline,
        "ingest_openbb_market_data",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("ingest should be skipped")),
    )
    monkeypatch.setattr(
        daily_research_pipeline,
        "run_local_ai_research",
        lambda **kwargs: {
            "memo_id": "memo_test",
            "status": "completed",
            "output_path": str(tmp_path / "memo.md"),
            "warnings": [],
            "error": None,
        },
    )

    result = run_daily_research_pipeline(symbols=["AAPL"], skip_ingest=True)

    assert result.status == "completed"
    assert result.local_ai_memo_id == "memo_test"
    assert result.analytics_report_path


def test_skip_ai_creates_analytics_only_run(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    monkeypatch.setattr(daily_research_pipeline, "REPORTS_DIR", tmp_path / "reports")
    initialize_database()
    monkeypatch.setattr(
        daily_research_pipeline,
        "ingest_openbb_market_data",
        lambda **kwargs: SimpleNamespace(
            run_id="openbb_test",
            status="completed",
            warnings=[],
            errors=[],
        ),
    )
    monkeypatch.setattr(
        daily_research_pipeline,
        "run_local_ai_research",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("AI should be skipped")),
    )

    result = run_daily_research_pipeline(symbols=["AAPL"], skip_ai=True)

    assert result.openbb_ingestion_run_id == "openbb_test"
    assert result.local_ai_memo_id is None
    assert result.status == "completed_with_warnings"


def test_local_ai_unavailable_saves_partial_failed_run(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    monkeypatch.setattr(daily_research_pipeline, "REPORTS_DIR", tmp_path / "reports")
    initialize_database()
    monkeypatch.setattr(
        daily_research_pipeline,
        "ingest_openbb_market_data",
        lambda **kwargs: SimpleNamespace(run_id="openbb_test", status="completed", warnings=[], errors=[]),
    )
    monkeypatch.setattr(
        daily_research_pipeline,
        "run_local_ai_research",
        lambda **kwargs: {
            "memo_id": "memo_failed",
            "status": "failed",
            "output_path": str(tmp_path / "memo.md"),
            "warnings": ["Ollama unavailable"],
            "error": "Ollama unavailable",
        },
    )

    result = run_daily_research_pipeline(symbols=["AAPL"])

    assert result.status == "partial_failed"
    assert result.local_ai_memo_id == "memo_failed"
    stored = fetch_dataframe("SELECT status, local_ai_memo_id FROM daily_research_runs")
    assert stored.iloc[0]["status"] == "partial_failed"


def test_mocked_local_ai_success_creates_completed_run(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    monkeypatch.setattr(daily_research_pipeline, "REPORTS_DIR", tmp_path / "reports")
    initialize_database()
    monkeypatch.setattr(
        daily_research_pipeline,
        "ingest_openbb_market_data",
        lambda **kwargs: SimpleNamespace(run_id="openbb_test", status="completed", warnings=[], errors=[]),
    )
    monkeypatch.setattr(
        daily_research_pipeline,
        "run_local_ai_research",
        lambda **kwargs: {
            "memo_id": "memo_ok",
            "status": "completed",
            "output_path": str(tmp_path / "memo.md"),
            "warnings": [],
            "error": None,
        },
    )

    result = run_daily_research_pipeline(symbols=["AAPL"])

    assert result.status == "completed"
    assert result.local_ai_memo_id == "memo_ok"
    assert Path(result.analytics_report_path).exists()


def test_daily_run_metadata_includes_dedupe_and_local_ai_retry_fields(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    monkeypatch.setattr(daily_research_pipeline, "REPORTS_DIR", tmp_path / "reports")
    initialize_database()
    monkeypatch.setattr(
        daily_research_pipeline,
        "ingest_openbb_market_data",
        lambda **kwargs: SimpleNamespace(
            run_id="openbb_test",
            status="completed",
            warnings=[],
            errors=[],
            rows_inserted=0,
            rows_failed=0,
            rows_skipped_duplicate=2,
            rows_updated=0,
            dedupe_enabled=True,
        ),
    )
    monkeypatch.setattr(
        daily_research_pipeline,
        "run_local_ai_research",
        lambda **kwargs: {
            "memo_id": "memo_ok",
            "status": "completed",
            "output_path": str(tmp_path / "memo.md"),
            "warnings": [],
            "error": None,
            "preflight": {"status": "ok", "model_available": True},
            "retry_attempts_used": 1,
            "compact_retry_used": True,
            "local_ai_status": "ok",
            "model_available": True,
        },
    )

    result = run_daily_research_pipeline(symbols=["AAPL"])

    stored = fetch_dataframe("SELECT metadata_json FROM daily_research_runs WHERE run_id = ?", (result.run_id,))
    metadata = stored.iloc[0]["metadata_json"]
    assert '"fresh_openbb_ingestion_rows_skipped_duplicate": 2' in metadata
    assert '"fresh_openbb_ingestion_dedupe_enabled": true' in metadata
    assert '"local_ai_retry_attempts_used": 1' in metadata
    assert '"local_ai_compact_retry_used": true' in metadata


def test_daily_pipeline_has_no_order_surface() -> None:
    names = set(dir(daily_research_pipeline))

    assert not {"create_order", "place_order", "market_order", "limit_order", "buy_order", "sell_order"} & names


def test_daily_research_cli_argument_parsing() -> None:
    args = run_daily_research_cli.parse_args(
        [
            "--symbols",
            "AAPL",
            "MSFT",
            "--provider",
            "yfinance",
            "--interval",
            "1d",
            "--dry-run",
        ]
    )

    assert args.symbols == ["AAPL", "MSFT"]
    assert args.provider == "yfinance"
    assert args.interval == "1d"
    assert args.dry_run is True


def test_daily_dashboard_page_compiles() -> None:
    page = PROJECT_ROOT / "src" / "dashboard" / "pages" / "13_daily_research.py"

    compile(page.read_text(encoding="utf-8"), str(page), "exec")


def test_venv_runner_script_exists_and_uses_openbb_venv() -> None:
    script = PROJECT_ROOT / "scripts" / "run_daily_research_venv.ps1"
    text = script.read_text(encoding="utf-8")

    assert script.exists()
    assert ".venv-openbb\\Scripts\\python.exe" in text
    assert "run_daily_research.py" in text
    assert "localhost:11434/api/version" in text
    assert "qwen2.5:3b" in text


def test_task_scheduler_helper_defaults_to_venv_runner_and_print_only() -> None:
    script = PROJECT_ROOT / "scripts" / "create_daily_research_task.ps1"
    text = script.read_text(encoding="utf-8")

    assert "run_daily_research_venv.ps1" in text
    assert "Default behavior is print-only" in text
    assert "if ($Register)" in text
    assert "Register-ScheduledTask" in text
    assert "-Register -At" in text


def test_scheduler_helper_has_no_credential_storage_surface() -> None:
    text = (PROJECT_ROOT / "scripts" / "create_daily_research_task.ps1").read_text(encoding="utf-8").lower()

    assert "get-credential" not in text
    assert "-password" not in text
    assert "apikey" not in text


def test_daily_runner_has_no_order_or_live_trading_strings() -> None:
    text = (PROJECT_ROOT / "scripts" / "run_daily_research_venv.ps1").read_text(encoding="utf-8").lower()

    forbidden = {"create_order", "place_order", "market_order", "limit_order", "buy_order", "sell_order"}
    assert not forbidden & set(text.split())
    assert "live_trading_enabled: true" not in text


def test_openbb_dedupe_script_exists_and_defaults_to_dry_run() -> None:
    script = PROJECT_ROOT / "scripts" / "dedupe_openbb_market_data.py"
    text = script.read_text(encoding="utf-8")

    assert script.exists()
    assert "OpenBB market data dedupe dry-run. No rows were deleted." in text
    assert "--apply" in text
    assert "reports" in text.lower()


def _insert_openbb_row(symbol: str, timestamp: str, close: float) -> None:
    insert_dict(
        "openbb_market_data",
        {
            "id": f"{symbol}_{timestamp}",
            "symbol": symbol,
            "asset_class": "equity",
            "provider": "yfinance",
            "interval": "1d",
            "timestamp": timestamp,
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": 1000,
            "adjusted_close": close,
            "source": "openbb_adapter",
            "retrieved_at": "2026-01-01T00:00:00+00:00",
            "metadata_json": "{}",
        },
    )
