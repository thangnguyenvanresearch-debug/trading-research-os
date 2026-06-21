from __future__ import annotations

from html import escape
from typing import Iterable

import streamlit as st


_BADGE_KINDS = {"success", "warning", "danger", "neutral", "info"}


def inject_global_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --tro-bg: #0f1318;
            --tro-panel: #161c23;
            --tro-panel-soft: #1b232c;
            --tro-border: #303b47;
            --tro-text: #eef2f5;
            --tro-muted: #a6b0ba;
            --tro-green: #4fc38a;
            --tro-amber: #e2b45f;
            --tro-red: #e07777;
            --tro-blue: #6ba8e5;
        }

        [data-testid="stAppViewContainer"] {
            background: var(--tro-bg);
        }

        [data-testid="stHeader"] {
            background: rgba(15, 19, 24, 0.92);
            border-bottom: 1px solid var(--tro-border);
        }

        [data-testid="stSidebar"] {
            background: #12171d;
            border-right: 1px solid var(--tro-border);
        }

        [data-testid="stSidebarNav"] {
            display: none;
        }

        [data-testid="stSidebarContent"] {
            padding-top: 1rem;
        }

        .block-container {
            max-width: 1440px;
            padding-top: 1.5rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3, p, div, span, label {
            letter-spacing: 0;
        }

        .tro-sidebar-brand {
            border-bottom: 1px solid var(--tro-border);
            padding: 0.25rem 0 1rem 0;
            margin-bottom: 0.75rem;
        }

        .tro-sidebar-brand strong {
            color: var(--tro-text);
            font-size: 1.05rem;
        }

        .tro-sidebar-brand span {
            color: var(--tro-muted);
            font-size: 0.78rem;
        }

        .tro-nav-label {
            color: #7f8b96;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            margin: 1rem 0 0.25rem 0;
        }

        .tro-hero {
            background: var(--tro-panel);
            border: 1px solid var(--tro-border);
            border-left: 4px solid var(--tro-blue);
            border-radius: 6px;
            padding: 1.25rem 1.4rem;
            margin-bottom: 1rem;
        }

        .tro-hero h1 {
            color: var(--tro-text);
            font-size: 2rem;
            line-height: 1.15;
            margin: 0 0 0.4rem 0;
        }

        .tro-hero p {
            color: var(--tro-muted);
            font-size: 0.96rem;
            margin: 0;
            max-width: 920px;
        }

        .tro-badge-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
            margin-top: 0.85rem;
        }

        .tro-badge {
            display: inline-flex;
            align-items: center;
            border: 1px solid var(--tro-border);
            border-radius: 999px;
            padding: 0.22rem 0.58rem;
            font-size: 0.72rem;
            font-weight: 650;
            white-space: nowrap;
        }

        .tro-badge-success { color: #9ee0bd; background: #183527; border-color: #2e6b4b; }
        .tro-badge-warning { color: #f0d394; background: #3b301b; border-color: #78602d; }
        .tro-badge-danger { color: #efb0b0; background: #3a2022; border-color: #774146; }
        .tro-badge-info { color: #acd1f2; background: #1b3043; border-color: #365f83; }
        .tro-badge-neutral { color: #c3cbd2; background: #252c34; border-color: #46515d; }

        .tro-metric-card {
            background: var(--tro-panel);
            border: 1px solid var(--tro-border);
            border-radius: 6px;
            min-height: 132px;
            padding: 0.95rem 1rem;
            margin-bottom: 0.7rem;
        }

        .tro-metric-label {
            color: var(--tro-muted);
            font-size: 0.76rem;
            font-weight: 650;
            text-transform: uppercase;
            margin-bottom: 0.45rem;
        }

        .tro-metric-value {
            color: var(--tro-text);
            font-size: 1.35rem;
            font-weight: 720;
            line-height: 1.2;
            overflow-wrap: anywhere;
        }

        .tro-metric-help {
            color: var(--tro-muted);
            font-size: 0.78rem;
            margin-top: 0.55rem;
            line-height: 1.35;
        }

        .tro-section {
            border-bottom: 1px solid var(--tro-border);
            margin: 1.35rem 0 0.75rem 0;
            padding-bottom: 0.45rem;
        }

        .tro-section h2 {
            color: var(--tro-text);
            font-size: 1.12rem;
            margin: 0;
        }

        .tro-section p {
            color: var(--tro-muted);
            font-size: 0.82rem;
            margin: 0.2rem 0 0 0;
        }

        .tro-caveat {
            border: 1px solid var(--tro-border);
            border-radius: 6px;
            padding: 0.75rem 0.9rem;
            margin: 0.65rem 0;
            color: var(--tro-text);
            font-size: 0.84rem;
            line-height: 1.45;
        }

        .tro-caveat-warning { background: #302817; border-left: 4px solid var(--tro-amber); }
        .tro-caveat-danger { background: #321d20; border-left: 4px solid var(--tro-red); }
        .tro-caveat-info { background: #182b3b; border-left: 4px solid var(--tro-blue); }
        .tro-caveat-success { background: #173126; border-left: 4px solid var(--tro-green); }
        .tro-caveat-neutral { background: var(--tro-panel-soft); border-left: 4px solid #77838e; }

        [data-testid="stDataFrame"] {
            border: 1px solid var(--tro-border);
            border-radius: 6px;
            overflow: hidden;
        }

        [data-testid="stExpander"] {
            border: 1px solid var(--tro-border);
            border-radius: 6px;
            background: var(--tro-panel);
        }

        .stButton > button, [data-testid="stFormSubmitButton"] > button {
            border-radius: 6px;
            border: 1px solid #4a5968;
            min-height: 2.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def status_badge(text: object, kind: str = "neutral") -> str:
    normalized = kind if kind in _BADGE_KINDS else "neutral"
    return f'<span class="tro-badge tro-badge-{normalized}">{escape(str(text))}</span>'


def hero(title: str, subtitle: str, badges: Iterable[tuple[object, str] | object] | None = None) -> None:
    badge_html = ""
    if badges:
        items = []
        for badge in badges:
            if isinstance(badge, tuple):
                items.append(status_badge(badge[0], badge[1]))
            else:
                items.append(status_badge(badge))
        badge_html = f'<div class="tro-badge-row">{"".join(items)}</div>'
    st.markdown(
        f"""
        <div class="tro-hero">
            <h1>{escape(title)}</h1>
            <p>{escape(subtitle)}</p>
            {badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: object, status: tuple[object, str] | object | None = None, help_text: str | None = None) -> None:
    status_html = ""
    if status is not None:
        status_html = status_badge(status[0], status[1]) if isinstance(status, tuple) else status_badge(status)
    help_html = f'<div class="tro-metric-help">{escape(help_text)}</div>' if help_text else ""
    st.markdown(
        f"""
        <div class="tro-metric-card">
            <div class="tro-metric-label">{escape(label)}</div>
            <div class="tro-metric-value">{escape(str(value))}</div>
            <div class="tro-badge-row">{status_html}</div>
            {help_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str | None = None) -> None:
    subtitle_html = f"<p>{escape(subtitle)}</p>" if subtitle else ""
    st.markdown(
        f'<div class="tro-section"><h2>{escape(title)}</h2>{subtitle_html}</div>',
        unsafe_allow_html=True,
    )


def caveat_box(text: str, kind: str = "warning") -> None:
    normalized = kind if kind in _BADGE_KINDS else "warning"
    st.markdown(
        f'<div class="tro-caveat tro-caveat-{normalized}">{escape(text)}</div>',
        unsafe_allow_html=True,
    )


def compact_dataframe(df, height: int = 320, empty_message: str = "No records available.") -> None:
    if df is None or df.empty:
        st.info(empty_message)
        return
    display_df = df.copy()
    for column in display_df.select_dtypes(include=["object"]).columns:
        non_null_types = display_df[column].dropna().map(type).nunique()
        if non_null_types > 1:
            display_df[column] = display_df[column].map(lambda value: "" if value is None else str(value))
    st.dataframe(display_df, width="stretch", hide_index=True, height=height)


def sidebar_navigation() -> None:
    with st.sidebar:
        st.markdown(
            '<div class="tro-sidebar-brand"><strong>Trading Research OS</strong><br><span>Private research cockpit</span></div>',
            unsafe_allow_html=True,
        )
        _sidebar_group(
            "Core",
            [
                ("pages/00_research_control_center.py", "Research Control Center", "home"),
                ("pages/01_market_cockpit.py", "Market Cockpit", "monitoring"),
                ("pages/13_daily_research.py", "Daily Research", "calendar_today"),
            ],
        )
        _sidebar_group(
            "Research",
            [
                ("pages/02_strategy_factory.py", "Strategy Factory", "science"),
                ("pages/03_backtest_leaderboard.py", "Backtest Leaderboard", "leaderboard"),
                ("pages/04_risk_gate.py", "Risk Gate", "shield"),
            ],
        )
        _sidebar_group(
            "Data / AI",
            [
                ("pages/10_openbb_ingestion.py", "OpenBB Ingestion", "database"),
                ("pages/12_local_ai_research.py", "Local AI Research", "memory"),
            ],
        )
        _sidebar_group(
            "Engines / Labs",
            [
                ("pages/05_crypto_freqtrade.py", "Crypto Freqtrade", "currency_bitcoin"),
                ("pages/06_equity_lean_qlib.py", "Equity LEAN + Qlib", "account_balance"),
                ("pages/07_market_making_lab.py", "Market Making Lab", "experiment"),
                ("pages/08_arbitrage_scanner.py", "Arbitrage Scanner", "search"),
                ("pages/09_nautilus_future_engine.py", "Nautilus Future Engine", "construction"),
                ("pages/14_lean_backtests.py", "LEAN Backtests", "candlestick_chart"),
                ("pages/15_qlib_research.py", "Qlib Research", "psychology"),
            ],
        )
        st.caption("Research-only · Local-first · No order execution")


def _sidebar_group(label: str, pages: list[tuple[str, str, str]]) -> None:
    st.markdown(f'<div class="tro-nav-label">{escape(label)}</div>', unsafe_allow_html=True)
    for path, page_label, icon in pages:
        st.page_link(path, label=page_label, icon=f":material/{icon}:")


def setup_page() -> None:
    """Apply the shared visual shell to an entrypoint or multipage script."""
    inject_global_css()
    sidebar_navigation()
