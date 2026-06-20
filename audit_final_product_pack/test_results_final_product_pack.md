# Test Results Final Product Pack

## Commands

| Command | Result | Notes |
|---|---|---|
| `python -m compileall src scripts -q` | passed | No compile errors. |
| `python -m compileall src/dashboard -q` | passed | No dashboard compile errors. |
| `python -m pytest -q` | passed | `137 passed`. |
| `python scripts/health_check.py` | passed | Read-only health summary printed. |
| `python scripts/health_check.py --write-report --json` | passed | JSON output valid; markdown report written. |

## Health Check Summary

```text
db_reachable=True
openbb_total_rows=2230
latest_daily_run=daily_ccd5abf71f95 (completed_with_warnings)
latest_ai_memo=memo_527fb16be9b4 (completed)
latest_lean_run=lean_bt_3f8ecb692783 (skeleton_created)
latest_qlib_run=qlib_run_045090f920b8 (unavailable)
safety_unsafe_count=0
```

JSON/report command produced:

```text
reports/health/health_check_2026-06-19T201512_0000.md
```

DuckDB fallback warning appeared. This is expected and documented; SQLite fallback is acceptable for local demo/research.
