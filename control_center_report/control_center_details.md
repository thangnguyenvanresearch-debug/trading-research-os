# Control Center Details

## Commands Run

Compile:

```powershell
python -m compileall src scripts -q
python -m compileall src\dashboard -q
```

Result: passed.

Tests:

```powershell
python -m pytest -q
```

Result:

```text
129 passed in 28.92s
```

CLI smoke:

```powershell
python scripts\report_control_center_status.py
```

Result:

```text
Research Control Center
report_path=D:\AI2\QuantGit\trading-research-os\reports\control_center\control_center_status_2026-06-19T193840_0000.md
safety_unsafe_count=0
```

Dashboard HTTP check:

```text
URLError: [WinError 10061] connection refused
```

Safety grep:

- No unsafe enablement found.
- Hits are expected documentation/tests/config false flags, endpoint blocklists, or LEAN research-only skeleton references.

## DB Tables Read

The control center reads these tables when available:

- `openbb_market_data`
- `openbb_ingestion_runs`
- `daily_research_runs`
- `ai_research_memos`
- `lean_backtest_runs`
- `qlib_experiment_runs`
- `qlib_dataset_exports`
- `qlib_predictions`

Missing tables are handled as empty DataFrames instead of crashing.

## Generated Report Path

```text
D:\AI2\QuantGit\trading-research-os\reports\control_center\control_center_status_2026-06-19T193840_0000.md
```

## Current Status Notes

- OpenBB: local rows exist.
- Local AI: Ollama endpoint reported available during smoke.
- Daily Research: latest run status is `completed_with_warnings`.
- LEAN: CLI is detected, but executable backtest remains unverified from earlier Docker/runtime timeout.
- Qlib: package missing, dataset export available.
- Safety: config-derived checklist is safe.

## Dashboard Notes

Page added:

```text
src/dashboard/pages/00_research_control_center.py
```

Launch command documented:

```powershell
streamlit run src/dashboard/app.py
```

The page does not run ingestion/backtests/AI generation on load. It reads local DB/config and shows static rule-based next actions.

## Remaining Issues

1. Streamlit was not running during HTTP check.
2. Qlib true execution remains unavailable until Qlib is installed.
3. LEAN executable verification remains a separate Docker/runtime diagnostics task.
