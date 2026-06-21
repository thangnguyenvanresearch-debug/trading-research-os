# Test Results MVP Release

| Command | Result | Summary |
|---|---|---|
| `python -m compileall src scripts -q` | passed | No compile errors. |
| `python -m compileall src/dashboard -q` | passed | No dashboard compile errors. |
| `python -m pytest -q` | passed | `137 passed`. |
| `python scripts/health_check.py` | passed | DB reachable, OpenBB 2230 rows, unsafe count 0. |
| `python scripts/health_check.py --write-report --json` | passed | Valid JSON and markdown report created. |
| Dashboard HTTP smoke | passed | `http://localhost:8501` returned 200. |

## Health Details

- OpenBB rows: 2230.
- AAPL: 1115 rows.
- MSFT: 1115 rows.
- Duplicate groups: none reported.
- Latest daily run: `daily_ccd5abf71f95`, `completed_with_warnings`.
- Latest AI memo: `memo_527fb16be9b4`, `completed`.
- Local AI current service: unavailable.
- Latest LEAN artifact: `lean_bt_3f8ecb692783`, `skeleton_created`.
- Latest Qlib run: `qlib_run_045090f920b8`, `unavailable`.
- Safety unsafe count: 0.

DuckDB is unavailable; documented SQLite fallback was used.
