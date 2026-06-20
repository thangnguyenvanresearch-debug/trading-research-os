# Control Center Summary

## Files Changed

- `src/dashboard/control_center.py`
- `src/dashboard/pages/00_research_control_center.py`
- `src/dashboard/app.py`
- `scripts/report_control_center_status.py`
- `tests/test_control_center.py`
- `README.md`
- `control_center_report/control_center_summary.md`
- `control_center_report/control_center_details.md`
- `control_center_report/control_center_findings.json`

## Dashboard / Control Center Added

Added Streamlit page:

```text
src/dashboard/pages/00_research_control_center.py
```

The page is read-only and shows:

- system status cards
- engine registry table
- latest run/artifact table
- safety checklist
- OpenBB data health
- latest Qlib dataset
- latest LEAN artifact
- static next-action recommendations

No engine execution, credentials, cloud login, live trading, or order controls were added.

## Helper Module Added

Added:

```text
src/dashboard/control_center.py
```

Helper functions read local config/DB only and handle missing tables safely.

## CLI Report Added

Added:

```text
scripts/report_control_center_status.py
```

Smoke result:

```text
report_path=D:\AI2\QuantGit\trading-research-os\reports\control_center\control_center_status_2026-06-19T193840_0000.md
safety_unsafe_count=0
```

## Latest Engine Statuses

```json
{
  "openbb": {"status": "has_data", "rows": 2230},
  "local_ai": {"status": "available", "model": "qwen2.5:3b"},
  "daily_scheduler": {"status": "completed_with_warnings"},
  "lean": {"status": "ready", "cli": true, "safe_for_live": false},
  "qlib": {"status": "missing", "available": false, "safe_for_live": false},
  "safety": {"status": "safe"}
}
```

## Safety Checklist

All checklist items are safe:

- OpenAI API disabled
- ChatGPT OAuth disabled
- credentials disabled
- brokerage disabled
- live trading disabled
- futures disabled
- leverage disabled
- real orders disabled
- Qlib daily disabled by default
- LEAN daily disabled by default

## Tests

- `python -m compileall src scripts -q`: passed
- `python -m compileall src\dashboard -q`: passed
- `python -m pytest -q`: passed, `129 passed`

## Dashboard HTTP

HTTP check:

```text
URLError: [WinError 10061] connection refused
```

Streamlit was not running. Source compile passed; visual inspection is still manual after launch.

## Remaining Issues

- Dashboard visual inspection not performed because Streamlit was not running.
- Qlib package remains missing; dataset export works, true Qlib execution unverified.
- LEAN executable backtest remains future Docker/runtime diagnostics.
