# File-Level Findings OpenBB Dashboard

## `src/analytics/openbb_analytics.py`
Status: implemented.

- Provides local-only `load_openbb_prices()`.
- Provides return summary, pair comparison, and data quality functions.
- Handles empty frames safely.
- No OpenBB/provider external fetch found.
- Minor caveat: daily volatility only for exact `1d` interval string.

## `src/dashboard/pages/10_openbb_ingestion.py`
Status: implemented.

- Shows status, latest run, ingestion runs, summary, data quality, chart, correlation, previews.
- Reads local DB only.
- No fetch button, API key form, order controls, or live trading controls.
- Visual rendering not verified.

## `scripts/report_openbb_analytics.py`
Status: implemented.

- Reads local DB only.
- Supports `--symbols`, `--provider`, `--interval`, `--output`.
- Writes CSV report safely under `reports/openbb` by default.
- Does not mutate market data.
- No external provider calls.

## `tests/test_openbb_analytics.py`
Status: implemented.

- Covers summary, drawdown, duplicate timestamps, empty inputs, pair comparison, and no order surface.
- Does not require internet/OpenBB installed.

## `README.md`
Status: implemented.

- Documents OpenBB local analytics.
- States dashboard reads local DB only and does not fetch external data on page load.
- States analytics are descriptive, not trading advice, and do not place orders or enable live trading.
