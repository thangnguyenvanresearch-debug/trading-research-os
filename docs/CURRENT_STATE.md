# Current State

Snapshot date: 2026-06-20 local working session.

## Verification Summary

- Latest test result after final product pack validation: `137 passed`.
- Control Center status: read-only and safety status `safe`.
- OpenBB local rows: `2230`.
- OpenBB AAPL: `1115` rows, `1115` distinct timestamps.
- OpenBB MSFT: `1115` rows, `1115` distinct timestamps.
- Local AI status: available, model `qwen2.5:3b`.
- Daily scheduler task name: `TradingResearchOSDailyResearch`.
- Latest daily run from DB: `daily_ccd5abf71f95`, status `completed_with_warnings`.
- Latest completed Local AI memo: `memo_527fb16be9b4`, response length `1947`.
- LEAN status: CLI detected and skeleton available, but executable backtest is `executable_failed_timeout` and remains unverified.
- Latest LEAN run row: `lean_bt_3f8ecb692783`, status `skeleton_created`.
- Qlib status: package missing.
- Latest Qlib dataset export: `qlib_export_b9c5625b0de2`, status `exported`, rows `2220`, feature count `10`.
- Latest Qlib experiment run: `qlib_run_045090f920b8`, status `unavailable`.

## Known Limitations

- LEAN executable backtest is not verified until Docker/runtime execution succeeds.
- Qlib true trainer is not verified because Qlib is missing.
- Control Center reports latest daily DB run; it does not query actual Windows Task Scheduler state.
- DuckDB is optional; the environment may use SQLite fallback.
- Research outputs are not buy/sell recommendations.

## Recommended Next Work

- Keep the current state as a research-only checkpoint.
- Verify LEAN Docker/runtime execution separately, without cloud login or brokerage credentials.
- Install and verify Qlib in an isolated environment if true Qlib trainer execution is needed.
- Keep running `python scripts/health_check.py --write-report --json` before demos.
