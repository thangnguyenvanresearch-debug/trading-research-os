from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import core.database as database
from core.database import fetch_dataframe, initialize_database, insert_dict
from lean_brain import lean_adapter
from lean_brain.lean_project_builder import create_lean_research_project
from lean_brain.lean_runner import parse_lean_results, run_lean_backtest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def test_lean_project_skeleton_created(tmp_path) -> None:
    result = create_lean_research_project(
        "equal_weight_demo",
        ["AAPL", "MSFT"],
        output_dir=tmp_path,
        data_manifest_path=str(tmp_path / "manifest.json"),
    )

    project = Path(result["project_path"])
    assert (project / "README.md").exists()
    assert (project / "Main.py").exists()
    assert (project / "strategy_config.json").exists()
    assert (project / "config.json").exists()
    assert (project / "lean.json").exists()
    assert "research-only" in (project / "README.md").read_text(encoding="utf-8").lower()
    lean_config = (project / "lean.json").read_text(encoding="utf-8")
    assert '"live-mode": false' in lean_config
    assert "brokerage" not in lean_config.lower()


def test_runner_unavailable_path_saves_run_record_and_report(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    monkeypatch.setattr(lean_adapter.shutil, "which", lambda name: None)
    monkeypatch.setattr(lean_adapter, "PROJECT_ROOT", tmp_path / "no_lean_project")
    initialize_database()
    _insert_openbb_row("AAPL", "2024-01-01")

    result = run_lean_backtest(
        symbols=["AAPL"],
        provider="yfinance",
        interval="1d",
        strategy_name="equal_weight_demo",
        skip_run=False,
        config={
            "mode": "research_only",
            "output_dir": str(tmp_path / "generated" / "lean"),
            "reports_dir": str(tmp_path / "reports" / "lean"),
        },
    )

    assert result["status"] == "unavailable"
    assert Path(result["project_path"]).exists()
    assert Path(result["report_path"]).exists()
    stored = fetch_dataframe("SELECT run_id, status, report_path FROM lean_backtest_runs")
    assert stored.iloc[0]["run_id"] == result["run_id"]
    assert stored.iloc[0]["status"] == "unavailable"


def test_runner_skip_run_creates_skeleton_without_lean(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    monkeypatch.setattr(lean_adapter.shutil, "which", lambda name: None)
    initialize_database()
    _insert_openbb_row("AAPL", "2024-01-01")

    result = run_lean_backtest(
        symbols=["AAPL"],
        strategy_name="equal_weight_demo",
        skip_run=True,
        config={
            "mode": "research_only",
            "output_dir": str(tmp_path / "generated" / "lean"),
            "reports_dir": str(tmp_path / "reports" / "lean"),
        },
    )

    assert result["status"] == "skeleton_created"
    assert Path(result["manifest_path"]).exists()


def test_runner_command_uses_local_lean_config(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    initialize_database()
    _insert_openbb_row("AAPL", "2024-01-01")
    monkeypatch.setattr(
        "lean_brain.lean_runner.get_lean_status",
        lambda config=None: {
            "engine": "lean",
            "mode": "research_only",
            "available": True,
            "lean_cli_available": True,
            "lean_cli_path": "lean.exe",
            "docker_available": True,
            "safe_for_live": False,
            "status": "ready",
            "warnings": [],
            "errors": [],
        },
    )

    class Completed:
        returncode = 1
        stdout = ""
        stderr = "local test failure"

    monkeypatch.setattr("lean_brain.lean_runner.subprocess.run", lambda command, **kwargs: Completed())

    result = run_lean_backtest(
        symbols=["AAPL"],
        strategy_name="equal_weight_demo",
        config={
            "mode": "research_only",
            "output_dir": str(tmp_path / "generated" / "lean"),
            "reports_dir": str(tmp_path / "reports" / "lean"),
        },
    )

    stored = fetch_dataframe("SELECT command_text FROM lean_backtest_runs WHERE run_id = ?", (result["run_id"],))
    assert "--lean-config" in stored.iloc[0]["command_text"]
    assert result["status"] == "failed"


def test_parser_does_not_invent_metrics(tmp_path) -> None:
    result = parse_lean_results(tmp_path)

    assert result["metrics"] == {}
    assert result["warnings"]


def test_lean_cli_skip_run_parser(monkeypatch, tmp_path) -> None:
    spec = importlib.util.spec_from_file_location("run_lean_backtest_cli", SCRIPTS_DIR / "run_lean_backtest.py")
    cli = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(cli)

    args = cli.parse_args(["--symbols", "AAPL", "MSFT", "--strategy-name", "demo", "--skip-run"])

    assert args.symbols == ["AAPL", "MSFT"]
    assert args.strategy_name == "demo"
    assert args.skip_run is True


def test_lean_dashboard_page_compiles() -> None:
    page = PROJECT_ROOT / "src" / "dashboard" / "pages" / "14_lean_backtests.py"

    compile(page.read_text(encoding="utf-8"), str(page), "exec")


def test_lean_runtime_modules_have_no_order_or_cloud_login_surface() -> None:
    import lean_brain.lean_adapter as adapter
    import lean_brain.lean_runner as runner

    source = "\n".join(
        [
            adapter.__loader__.get_source(adapter.__name__),
            runner.__loader__.get_source(runner.__name__),
        ]
    ).lower()
    assert "openai_api_key" not in source
    assert "create_order" not in source
    assert "place_order" not in source
    assert "market_order" not in source
    assert "limit_order" not in source


def _insert_openbb_row(symbol: str, timestamp: str) -> None:
    insert_dict(
        "openbb_market_data",
        {
            "id": f"{symbol}_{timestamp}",
            "symbol": symbol,
            "asset_class": "equity",
            "provider": "yfinance",
            "interval": "1d",
            "timestamp": timestamp,
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
