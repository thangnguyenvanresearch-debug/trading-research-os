# Control Center Accuracy Fix Summary

## Files changed

- `src/dashboard/control_center.py`
- `src/dashboard/pages/00_research_control_center.py`
- `scripts/report_control_center_status.py`
- `tests/test_control_center.py`
- `README.md`

## Fixes implemented

- LEAN is no longer reported as simply `ready`.
- LEAN status now exposes `cli_detected`, `skeleton_available`, `executable_verified`, and `latest_executable_status`.
- Latest observed LEAN executable state is reported as `executable_failed_timeout`; executable LEAN backtest remains unverified.
- Daily status is now labeled `latest_daily_run`, sourced from `daily_research_runs`.
- Scheduler state is explicitly `not_verified` unless queried separately.
- Warning/error summaries are compacted and truncated to about 240 characters.
- README repeats LEAN/Qlib caveats and confirms the Control Center is read-only.

## Validation

- `python -m compileall src scripts -q`: passed.
- `python -m compileall src/dashboard -q`: passed.
- `python -m pytest -q`: passed, 132 tests.
- `python scripts/report_control_center_status.py`: passed.

## Current status wording

- OpenBB: `has_data`, rows `2230`.
- Local AI: `available`, model `qwen2.5:3b`.
- Latest daily run: `completed_with_warnings`, scheduler state `not_verified`.
- LEAN: `executable_failed_timeout`, CLI detected, skeleton available, executable verified `false`.
- Qlib: `missing`, safe for live `false`.
- Safety: `safe`.

## Remaining issues

- LEAN executable backtest remains unverified until Docker/runtime execution succeeds.
- Qlib true trainer remains future work while Qlib is not installed.
- Windows Task Scheduler state is not queried by the Control Center page.

## Safety

No OpenAI API, ChatGPT OAuth, cookies, browser automation, password handling, cloud credentials, brokerage credentials, live trading, futures, leverage, or real orders were added.
