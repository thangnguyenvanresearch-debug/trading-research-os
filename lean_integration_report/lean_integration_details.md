# LEAN Integration Details

## Commands run

### Compile

```powershell
python -m compileall src scripts -q
python -m compileall src/dashboard -q
```

Result: passed.

### Tests

```powershell
python -m pytest -q
```

Result:

```text
102 passed in 17.08s
```

### Skeleton smoke test

```powershell
python scripts\run_lean_backtest.py --symbols AAPL MSFT --provider yfinance --interval 1d --strategy-name equal_weight_demo --skip-run
```

Output:

```text
run_id=lean_bt_f9a4224eb9c6
status=skeleton_created
project_path=D:\AI2\QuantGit\trading-research-os\data\generated\lean\projects\equal_weight_demo_lean_495bed575415
report_path=D:\AI2\QuantGit\trading-research-os\reports\lean\lean_bt_f9a4224eb9c6_equal_weight_demo.md
warnings=["LEAN run skipped by request; research-only skeleton was created."]
errors=[]
```

### Normal wrapper smoke test

```powershell
python scripts\run_lean_backtest.py --symbols AAPL MSFT --provider yfinance --interval 1d --strategy-name equal_weight_demo
```

Output:

```text
run_id=lean_bt_496f6c073884
status=unavailable
project_path=D:\AI2\QuantGit\trading-research-os\data\generated\lean\projects\equal_weight_demo_lean_d41360a694ff
report_path=D:\AI2\QuantGit\trading-research-os\reports\lean\lean_bt_496f6c073884_equal_weight_demo.md
warnings=["LEAN CLI is not installed; only data export and research skeleton generation are available."]
errors=[]
```

### LEAN status

```json
{
  "engine": "lean",
  "mode": "research_only",
  "available": false,
  "lean_cli_available": false,
  "docker_available": true,
  "safe_for_live": false,
  "status": "missing",
  "warnings": [
    "LEAN CLI is not installed; only data export and research skeleton generation are available."
  ],
  "errors": []
}
```

### DB verification

Latest LEAN runs:

```text
lean_bt_496f6c073884 unavailable
lean_bt_f9a4224eb9c6 skeleton_created
```

Metrics table:

```text
No rows.
```

This is correct because LEAN CLI did not execute and no result/statistics JSON was available.

OpenBB source data:

```text
AAPL yfinance 1d rows=1115 distinct_timestamps=1115
MSFT yfinance 1d rows=1115 distinct_timestamps=1115
```

### Exported data

Manifest:

```text
D:\AI2\QuantGit\trading-research-os\data\generated\lean\data\data_manifest.json
```

Manifest summary:

```json
{
  "label": "LEAN research bridge data",
  "provider": "yfinance",
  "interval": "1d",
  "symbols": {
    "AAPL": {
      "rows": 1115
    },
    "MSFT": {
      "rows": 1115
    }
  },
  "warnings": []
}
```

### Generated project path

Latest project:

```text
D:\AI2\QuantGit\trading-research-os\data\generated\lean\projects\equal_weight_demo_lean_d41360a694ff
```

Contains:

- `README.md`
- `strategy_config.json`
- `Main.py`
- `local_data_manifest.json`

The generated files are labeled research-only and do not configure brokerage credentials, QuantConnect cloud login, live mode, futures, leverage, or real orders.

### Dashboard check

```powershell
python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8501', timeout=10).status)"
```

Result:

```text
200
```

Page added:

```text
src/dashboard/pages/14_lean_backtests.py
```

The page shows LEAN CLI/Docker status, latest runs, project/report paths, warnings/errors, and parsed metrics when available.

### Safety grep

Search scope:

```text
configs src scripts tests README.md
```

Result: no unsafe enablement found.

Observed matches were limited to:

- negative README statements
- config flags set to false
- tests asserting forbidden surfaces are absent
- Local AI forbidden-host denylist
- OpenBB redaction/provider warning text
- LEAN research-only warnings and config enforcement

## Remaining issues

- Install LEAN CLI locally before expecting executable LEAN backtests.
- Keep QuantConnect cloud login and brokerage credentials disabled.
- The project skeleton uses LEAN-style APIs for local backtesting only; successful execution was not verified because LEAN CLI is missing.
