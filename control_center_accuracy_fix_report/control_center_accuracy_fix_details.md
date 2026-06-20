# Control Center Accuracy Fix Details

## Commands run

```text
python -m compileall src scripts -q
python -m compileall src/dashboard -q
python -m pytest -q
python scripts/report_control_center_status.py
```

Results:

- Compile checks passed.
- Pytest passed with `132 passed`.
- CLI report wrote `reports/control_center/control_center_status_2026-06-19T200604_0000.md`.
- CLI output reported `lean_executable_verified=False` and `daily_scheduler_state=not_verified`.

## Implementation notes

`src/dashboard/control_center.py` now summarizes LEAN separately from raw adapter status. If the LEAN CLI is detected but the most recent executable run failed or timed out, the Control Center reports `executable_failed_timeout` or `cli_detected_executable_unverified`, not `ready`.

Daily pipeline status now uses the key `latest_daily_run`. It is explicitly marked as sourced from `daily_research_runs`; scheduler activity is not inferred.

Warning and error summaries are normalized and truncated through `summarize_text(...)`. This prevents long JSON/text blobs from overwhelming dashboard tables and CLI reports.

`src/dashboard/pages/00_research_control_center.py` remains read-only. It does not add buttons that execute engines, does not add credential inputs, and does not add live/order controls.

`README.md` now states that LEAN executable backtest remains unverified until Docker/runtime succeeds, and that Qlib true trainer remains future work while Qlib is missing.

## Safety grep

A corrected safety grep over `configs`, `src`, `scripts`, `tests`, and `README.md` found only existing defensive/config/documentation/test references such as disabled flags, forbidden-term tests, redaction/guard code, and LEAN research-only skeleton text. No new unsafe enablement was found.

## Remaining issues

- LEAN executable backtest is still not verified.
- Qlib execution is still not verified because Qlib is missing.
- Control Center does not query actual Windows Task Scheduler state; it only shows latest daily pipeline DB state.
