# UI Redesign v0.3 File Changes

## Added

- `src/dashboard/components/ui.py`: shared visual shell, CSS, navigation, hero, cards, badges, caveats, and compact tables.
- `tests/test_dashboard_visual_ux.py`: source and optional-Plotly safeguards for the redesign.
- `ui_redesign_v03_report/*`: implementation, test, and manual-check reports.

## Modified

- `src/dashboard/streamlit_app.py`: branded shell and compact overview.
- `src/dashboard/pages/00_research_control_center.py`: six-card cockpit and detail expanders.
- `src/dashboard/pages/01_market_cockpit.py`: market summary cards and raw-data expanders.
- `src/dashboard/pages/02_strategy_factory.py`: specification summary and bounded artifacts.
- `src/dashboard/pages/03_backtest_leaderboard.py`: strategy/risk summary before leaderboard.
- `src/dashboard/pages/04_risk_gate.py`: prominent selected decision and rejection framing.
- `src/dashboard/pages/05_crypto_freqtrade.py`: engine summary and bounded tables.
- `src/dashboard/pages/06_equity_lean_qlib.py`: shared shell and engine caveats.
- `src/dashboard/pages/07_market_making_lab.py`: simulation framing.
- `src/dashboard/pages/08_arbitrage_scanner.py`: alert-only framing.
- `src/dashboard/pages/09_nautilus_future_engine.py`: future-work framing.
- `src/dashboard/pages/10_openbb_ingestion.py`: local-data cards, quality overview, and preview expanders.
- `src/dashboard/pages/12_local_ai_research.py`: local runtime cards and friendly Ollama setup.
- `src/dashboard/pages/13_daily_research.py`: DB-run caveat, summary cards, and history expander.
- `src/dashboard/pages/14_lean_backtests.py`: executable-unverified status made visually explicit.
- `src/dashboard/pages/15_qlib_research.py`: dataset/trainer distinction made visually explicit.

No engine, schema, scheduler, or trading-logic files were modified.

