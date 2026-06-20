# Daily Research Final Readiness Summary

## Duplicate dry-run result

- Command: `.\.venv-openbb\Scripts\python.exe scripts\dedupe_openbb_market_data.py --limit 20`
- Result: passed.
- Dry-run showed exact duplicate groups keyed by:
  `symbol`, `asset_class`, `provider`, `interval`, `timestamp`.
- No rows were deleted during dry-run.

## Row counts before cleanup

| Symbol | Provider | Interval | Rows | Distinct Timestamps |
|---|---|---|---:|---:|
| AAPL | yfinance | 1d | 2230 | 1115 |
| MSFT | yfinance | 1d | 2230 | 1115 |

## Duplicate cleanup result

- Command: `.\.venv-openbb\Scripts\python.exe scripts\dedupe_openbb_market_data.py --apply`
- Result: passed.
- Duplicate rows found: `4460`
- Rows deleted: `2230`
- Rows kept: `2230`
- Backup path:
  `D:\AI2\QuantGit\trading-research-os\reports\maintenance\openbb_market_data_duplicates_2026-06-14T150431_0000.csv`

No OpenBB ingestion history, AI memos, daily research run history, or non-duplicate market rows were deleted.

## Row counts after cleanup

| Symbol | Provider | Interval | Rows | Distinct Timestamps |
|---|---|---|---:|---:|
| AAPL | yfinance | 1d | 1115 | 1115 |
| MSFT | yfinance | 1d | 1115 | 1115 |

## Ollama service status

- Ollama service: available.
- Version endpoint returned: `0.30.8`.
- `/api/tags` showed `qwen2.5:3b` installed.

## Pipeline rerun result

- Command: `powershell -ExecutionPolicy Bypass -File scripts\run_daily_research_venv.ps1`
- Latest run_id: `daily_262063e1ff1f`
- Status: `completed_with_warnings`
- Warning: context markdown was truncated to `12000` characters.
- OpenBB ingestion status: `completed`
- rows_inserted: `0`
- rows_failed: `0`
- rows_skipped_duplicate: `2230`
- dedupe_enabled: `true`
- Local AI preflight: `ok`
- Local AI model available: `true`
- Local AI status: `ok`

## Latest memo

- memo_id: `memo_d03ffe674cfe`
- status: `completed`
- model: `qwen2.5:3b`
- response length: `588`
- report path:
  `D:\AI2\QuantGit\trading-research-os\reports\local_ai\memo_d03ffe674cfe_daily_research_note.md`

## Scheduler readiness

- `scripts/run_daily_research_venv.ps1` exists and uses `.venv-openbb\Scripts\python.exe`.
- `scripts/create_daily_research_task.ps1` uses the venv runner.
- Default scheduler helper behavior is print-only.
- `-Register` is required to create a Windows scheduled task.
- Print-only helper ran successfully and did not register a task.

Register later with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\create_daily_research_task.ps1 -Register -At "08:30"
```

This command was not run.

## Dashboard check

- `http://localhost:8501` returned HTTP `200`.
- Manual browser inspection is still recommended for pages:
  - `13_daily_research`
  - `12_local_ai_research`

## Test result

- `.\.venv-openbb\Scripts\python.exe -m compileall src scripts -q`: passed
- `.\.venv-openbb\Scripts\python.exe -m pytest -q`: passed, `86 passed`

## Safety confirmation

No OpenAI API, ChatGPT OAuth, cookies, browser automation, password handling, live trading, futures, leverage, real orders, or buy/sell execution features were added.

Safety grep found only negative documentation/assertions, config false flags, local denylist checks, provider warning text, and redaction regex references.

## Remaining issues

- None blocking scheduler readiness.
- DuckDB is unavailable in this environment, so the project continues to use SQLite fallback with a warning. This is acceptable for local demo/research but DuckDB is recommended for larger analytical workloads.
