from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import core.database as database
from core.database import initialize_database


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def _load_health_check_module():
    spec = importlib.util.spec_from_file_location("health_check_cli", SCRIPTS_DIR / "health_check.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_health_check_imports() -> None:
    module = _load_health_check_module()

    assert module.main
    assert module.collect_health_status


def test_health_check_json_shape_with_missing_tables(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "missing.sqlite")
    module = _load_health_check_module()

    status = module.collect_health_status()

    assert set(status).issuperset(
        {
            "db_reachable",
            "engine_statuses",
            "openbb_total_rows",
            "latest_daily_run",
            "latest_ai_memo",
            "latest_lean_run",
            "latest_qlib_run",
            "safety_unsafe_count",
        }
    )
    assert status["db_reachable"] is True
    assert status["openbb_total_rows"] == 0


def test_health_check_report_writes_markdown(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    initialize_database()
    module = _load_health_check_module()

    status = module.collect_health_status()
    path = module.write_health_report(status, output_dir=tmp_path / "health")

    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Trading Research OS Health Check" in text
    assert "No engines were executed" in text


def test_health_check_cli_json_output(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    initialize_database()
    module = _load_health_check_module()

    assert module.main(["--json"]) == 0
    captured = capsys.readouterr().out

    assert '"db_reachable": true' in captured
    assert '"engine_statuses"' in captured


def test_health_check_has_no_unsafe_controls() -> None:
    source = (SCRIPTS_DIR / "health_check.py").read_text(encoding="utf-8").lower()

    for forbidden in [
        "openai_api_key",
        "api.openai.com",
        "chatgpt.com/auth",
        "create_order",
        "place_order",
        "market_order",
        "limit_order",
        "buy_order",
        "sell_order",
    ]:
        assert forbidden not in source
