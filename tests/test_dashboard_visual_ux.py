from __future__ import annotations

import builtins
import importlib.util
from pathlib import Path

import streamlit  # Load Streamlit before blocking the optional Plotly import.


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = PROJECT_ROOT / "src" / "dashboard"


def test_shared_visual_system_is_present() -> None:
    source = (DASHBOARD / "components" / "ui.py").read_text(encoding="utf-8")

    for helper in [
        "def inject_global_css",
        "def hero",
        "def metric_card",
        "def status_badge",
        "def section_header",
        "def caveat_box",
        "def compact_dataframe",
        "def sidebar_navigation",
    ]:
        assert helper in source
    assert "Trading Research OS" in source
    assert "Private research cockpit" in source


def test_control_center_is_visibly_summary_first() -> None:
    source = (DASHBOARD / "pages" / "00_research_control_center.py").read_text(encoding="utf-8")

    assert 'hero(' in source
    assert "What this means" in source
    assert source.count("metric_card(") >= 6
    assert 'st.expander("Raw Debug Tables"' in source
    assert "Research-only. No live trading. No orders." in source


def test_every_dashboard_page_uses_shared_shell() -> None:
    pages = sorted((DASHBOARD / "pages").glob("*.py"))

    assert pages
    for page in pages:
        source = page.read_text(encoding="utf-8")
        assert "setup_page()" in source, page.name


def test_market_cockpit_keeps_plotly_optional(monkeypatch) -> None:
    real_import = builtins.__import__

    def blocked_import(name, *args, **kwargs):
        if name.startswith("plotly"):
            raise ImportError("plotly intentionally unavailable")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)
    spec = importlib.util.spec_from_file_location("visual_ux_charts", DASHBOARD / "components" / "charts.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    assert module.plotly_available() is False
    cockpit = (DASHBOARD / "pages" / "01_market_cockpit.py").read_text(encoding="utf-8")
    assert "price_chart" in cockpit
    assert "import plotly" not in cockpit.lower()


def test_runtime_ui_has_no_forbidden_execution_controls() -> None:
    runtime_sources = [DASHBOARD / "streamlit_app.py", *sorted((DASHBOARD / "pages").glob("*.py"))]
    combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in runtime_sources)

    forbidden = [
        "create_order(",
        "place_order(",
        "live_trading_enabled=true",
        "real_orders_enabled=true",
        "openai_api_key",
        "broker_password",
        "broker credential input",
    ]
    for term in forbidden:
        assert term not in combined
