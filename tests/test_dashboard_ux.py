from __future__ import annotations

import builtins
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import streamlit  # Ensure Streamlit itself loads before Plotly imports are blocked.


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = PROJECT_ROOT / "src" / "dashboard"


def test_charts_import_and_fallback_without_plotly(monkeypatch) -> None:
    real_import = builtins.__import__

    def blocked_import(name, *args, **kwargs):
        if name.startswith("plotly"):
            raise ImportError("plotly blocked for fallback test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)
    spec = importlib.util.spec_from_file_location("charts_without_plotly", DASHBOARD / "components" / "charts.py")
    charts = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(charts)
    assert charts.plotly_available() is False

    charts.st = MagicMock()
    charts.st.expander.return_value.__enter__.return_value = MagicMock()
    frame = pd.DataFrame(
        [{"timestamp": "2026-01-01", "open": 1, "high": 2, "low": 1, "close": 2, "volume": 10}]
    )
    charts.price_chart(frame, "Research price")

    charts.st.warning.assert_called_once_with("Plotly is not installed; showing native Streamlit fallback.")
    charts.st.line_chart.assert_called_once()


def test_research_wording_and_control_center_layout() -> None:
    signal_source = (DASHBOARD / "components" / "signal_cards.py").read_text(encoding="utf-8")
    control_source = (DASHBOARD / "pages" / "00_research_control_center.py").read_text(encoding="utf-8")

    assert "Research Action" in signal_source
    assert "Risk Gate Result" in signal_source
    assert "What this means" in control_source
    assert 'st.expander("Engine Registry"' in control_source
    assert 'st.expander("Latest Runs And Artifacts"' in control_source
    assert 'st.expander("Safety Details"' in control_source


def test_local_ai_unavailable_guidance_is_local_only() -> None:
    source = (DASHBOARD / "pages" / "12_local_ai_research.py").read_text(encoding="utf-8").lower()

    assert "ollama serve" in source
    assert "ollama list" in source
    assert "qwen2.5:3b" in source
    assert "disabled=not bool(status.get" in source
    for forbidden in ["openai_api_key", "api.openai.com", "chatgpt.com/auth", "place_order", "create_order"]:
        assert forbidden not in source


def test_dashboard_pages_compile_after_ux_cleanup() -> None:
    paths = [
        DASHBOARD / "streamlit_app.py",
        DASHBOARD / "pages" / "00_research_control_center.py",
        DASHBOARD / "pages" / "01_market_cockpit.py",
        DASHBOARD / "pages" / "03_backtest_leaderboard.py",
        DASHBOARD / "pages" / "04_risk_gate.py",
        DASHBOARD / "pages" / "05_crypto_freqtrade.py",
        DASHBOARD / "pages" / "12_local_ai_research.py",
        DASHBOARD / "pages" / "14_lean_backtests.py",
        DASHBOARD / "pages" / "15_qlib_research.py",
    ]

    for path in paths:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
