# Test Results - Control Center Audit

## Compile

```powershell
python -m compileall src scripts -q
```

Result: **passed**

```powershell
python -m compileall src\dashboard -q
```

Result: **passed**

## Pytest

```powershell
python -m pytest -q
```

Result:

```text
129 passed in 27.91s
```

## CLI Report Smoke

```powershell
python scripts\report_control_center_status.py
```

Result: **passed**

Output summary:

```text
Research Control Center
report_path=D:\AI2\QuantGit\trading-research-os\reports\control_center\control_center_status_2026-06-19T195003_0000.md
safety_unsafe_count=0
```

Latest statuses:

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

## DB Verification

Queries passed.

Summary:

- OpenBB:
  - AAPL/yfinance/1d: 1115 rows, 1115 distinct timestamps
  - MSFT/yfinance/1d: 1115 rows, 1115 distinct timestamps
- Daily latest: `completed_with_warnings`
- Local AI latest memo: `completed`, response length 1947
- LEAN latest: `skeleton_created`; earlier executable run failed timeout
- Qlib latest: `unavailable`

## Dashboard HTTP

```text
URLError: [WinError 10061] connection refused
```

Streamlit was not running. Source compile passed.

## Safety Grep

No unsafe enablement found. Hits are expected docs/tests/config false flags/blocklists/research-only LEAN skeleton references.
