# UI Cleanup v0.2 File Changes

## Dashboard Components

- `src/dashboard/components/charts.py`: optional Plotly import and native fallback.
- `src/dashboard/components/signal_cards.py`: research-oriented labels.
- `src/dashboard/components/tables.py`: bounded default table height.

## Core Pages

- `src/dashboard/streamlit_app.py`: private research title, safety caption, sidebar page guide, research-decision wording.
- `src/dashboard/pages/00_research_control_center.py`: interpretation section, cleaner first viewport, detail expanders.
- `src/dashboard/pages/01_market_cockpit.py`: research-only caption and latest research decision wording.

## Research / Data Pages

- `src/dashboard/pages/03_backtest_leaderboard.py`: summary metrics and bounded leaderboard.
- `src/dashboard/pages/04_risk_gate.py`: Risk Gate wording and collapsed review history.
- `src/dashboard/pages/05_crypto_freqtrade.py`: summary metrics and expandable tables.
- `src/dashboard/pages/10_openbb_ingestion.py`: live execution wording.
- `src/dashboard/pages/12_local_ai_research.py`: unavailable guidance, disabled run button, memo summary/history expander.
- `src/dashboard/pages/14_lean_backtests.py`: executable caveat, live execution wording, summary/history expanders.
- `src/dashboard/pages/15_qlib_research.py`: trainer caveat, live execution wording, summary/history expanders.

## Tests And Reports

- `tests/test_dashboard_ux.py`: Plotly fallback, wording, guidance, and compile coverage.
- `ui_cleanup_v02_report/*`: implementation and validation report.

No trading logic, engine implementation, database schema, scheduler behavior, credential surface, or order capability was changed.
