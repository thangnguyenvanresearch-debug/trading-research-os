from __future__ import annotations

from pathlib import Path

import pytest

from lean_brain import lean_adapter
from lean_brain.lean_adapter import assert_lean_research_only, get_lean_status


def test_lean_unavailable_status_is_safe(monkeypatch) -> None:
    monkeypatch.setattr(lean_adapter.shutil, "which", lambda name: None)
    monkeypatch.setattr(lean_adapter, "PROJECT_ROOT", Path("C:/definitely/no/lean/project"))

    status = get_lean_status({"mode": "research_only"})

    assert status["engine"] == "lean"
    assert status["lean_cli_available"] is False
    assert status["docker_available"] is False
    assert status["safe_for_live"] is False
    assert status["status"] == "missing"


def test_lean_status_detects_project_venv_cli(monkeypatch, tmp_path) -> None:
    fake_root = tmp_path / "project"
    scripts_dir = fake_root / ".venv-openbb" / "Scripts"
    scripts_dir.mkdir(parents=True)
    lean_exe = scripts_dir / "lean.exe"
    lean_exe.write_text("", encoding="utf-8")
    monkeypatch.setattr(lean_adapter, "PROJECT_ROOT", fake_root)
    monkeypatch.setattr(lean_adapter.shutil, "which", lambda name: "docker.exe" if name == "docker" else None)

    status = get_lean_status({"mode": "research_only"})

    assert status["lean_cli_available"] is True
    assert status["lean_cli_path"] == str(lean_exe)
    assert status["status"] == "ready"


@pytest.mark.parametrize(
    "key",
    [
        "allow_live_trading",
        "allow_brokerage_credentials",
        "allow_quantconnect_cloud",
        "allow_real_orders",
        "allow_futures",
        "allow_leverage",
    ],
)
def test_lean_research_only_rejects_unsafe_flags(key: str) -> None:
    config = {"mode": "research_only", key: True}

    with pytest.raises(ValueError):
        assert_lean_research_only(config)


def test_lean_research_only_rejects_non_research_mode() -> None:
    with pytest.raises(ValueError):
        assert_lean_research_only({"mode": "live"})
