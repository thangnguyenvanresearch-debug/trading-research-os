from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd

import core.database as database
from core.database import fetch_dataframe, initialize_database, insert_dict
from qlib_brain import qlib_adapter
from qlib_brain.qlib_runner import run_qlib_experiment


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def test_qlib_skip_run_creates_dataset(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    initialize_database()
    _insert_rows("AAPL")

    result = run_qlib_experiment(
        symbols=["AAPL"],
        skip_run=True,
        config={
            "mode": "research_only",
            "output_dir": str(tmp_path / "generated" / "qlib"),
            "reports_dir": str(tmp_path / "reports" / "qlib"),
        },
    )

    assert result["status"] == "dataset_exported"
    assert Path(result["features_path"]).exists()
    assert Path(result["report_path"]).exists()


def test_qlib_unavailable_path_saves_run_without_predictions(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    monkeypatch.setattr(qlib_adapter.importlib.util, "find_spec", lambda name: None)
    initialize_database()
    _insert_rows("AAPL")

    result = run_qlib_experiment(
        symbols=["AAPL"],
        skip_run=False,
        config={
            "mode": "research_only",
            "output_dir": str(tmp_path / "generated" / "qlib"),
            "reports_dir": str(tmp_path / "reports" / "qlib"),
        },
    )

    assert result["status"] == "unavailable"
    assert result["metrics"] == {}
    assert result["predictions_count"] == 0
    runs = fetch_dataframe("SELECT run_id, status, qlib_available FROM qlib_experiment_runs")
    assert runs.iloc[0]["run_id"] == result["run_id"]
    assert runs.iloc[0]["qlib_available"] == 0
    predictions = fetch_dataframe("SELECT * FROM qlib_predictions")
    assert predictions.empty


def test_qlib_cli_parser() -> None:
    spec = importlib.util.spec_from_file_location("run_qlib_experiment_cli", SCRIPTS_DIR / "run_qlib_experiment.py")
    cli = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(cli)

    args = cli.parse_args(["--symbols", "AAPL", "MSFT", "--experiment-name", "demo", "--skip-run"])

    assert args.symbols == ["AAPL", "MSFT"]
    assert args.experiment_name == "demo"
    assert args.skip_run is True


def test_qlib_dashboard_page_compiles() -> None:
    page = PROJECT_ROOT / "src" / "dashboard" / "pages" / "15_qlib_research.py"

    compile(page.read_text(encoding="utf-8"), str(page), "exec")


def test_qlib_runtime_modules_have_no_live_order_or_credential_surface() -> None:
    import qlib_brain.qlib_adapter as adapter
    import qlib_brain.qlib_runner as runner

    source = "\n".join(
        [
            adapter.__loader__.get_source(adapter.__name__),
            runner.__loader__.get_source(runner.__name__),
        ]
    ).lower()
    for forbidden in ["openai_api_key", "create_order", "place_order", "market_order", "limit_order", "lean login"]:
        assert forbidden not in source


def _insert_rows(symbol: str) -> None:
    for index in range(40):
        close = 100 + index
        timestamp = (pd.Timestamp("2024-01-01") + pd.Timedelta(days=index)).strftime("%Y-%m-%d")
        insert_dict(
            "openbb_market_data",
            {
                "id": f"{symbol}_{index}",
                "symbol": symbol,
                "asset_class": "equity",
                "provider": "yfinance",
                "interval": "1d",
                "timestamp": timestamp,
                "open": close,
                "high": close + 1,
                "low": close - 1,
                "close": close,
                "volume": 1000 + index,
                "adjusted_close": close,
                "source": "test",
                "retrieved_at": "2026-01-01T00:00:00+00:00",
                "metadata_json": "{}",
            },
        )
