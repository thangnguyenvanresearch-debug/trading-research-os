# Test Results - LEAN CLI Compatibility Patch

## Compile

Command:

```powershell
.\.venv-openbb\Scripts\python.exe -m compileall src scripts -q
```

Result: **passed**

Command:

```powershell
.\.venv-openbb\Scripts\python.exe -m compileall src\dashboard -q
```

Result: **passed**

## Pytest

Command:

```powershell
.\.venv-openbb\Scripts\python.exe -m pytest -q
```

Result:

```text
104 passed in 24.56s
```

## LEAN CLI

Command:

```powershell
.\.venv-openbb\Scripts\lean.exe --version
```

Result:

```text
lean 1.0.225
```

## Docker

Command:

```powershell
docker info --format '{{json .ServerVersion}}'
```

Result: **failed**

Summary:

```text
failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine
```

Docker CLI exists, but daemon was not reachable during this audit.

## Skip-run Smoke

Command:

```powershell
.\.venv-openbb\Scripts\python.exe scripts\run_lean_backtest.py --symbols AAPL MSFT --provider yfinance --interval 1d --strategy-name equal_weight_demo --skip-run
```

Result: **passed**

Output summary:

- run_id: `lean_bt_3f8ecb692783`
- status: `skeleton_created`
- project_path: `D:\AI2\QuantGit\trading-research-os\data\generated\lean\projects\equal_weight_demo_lean_ca37bf610253`
- report_path: `D:\AI2\QuantGit\trading-research-os\reports\lean\lean_bt_3f8ecb692783_equal_weight_demo.md`
- warnings: `["LEAN run skipped by request; research-only skeleton was created."]`
- errors: `[]`

## DB Verification

Result:

- latest skip-run is recorded.
- timeout run `lean_bt_f4d0947fa6ef` is recorded as `failed`.
- `lean_backtest_metrics` is empty.
- No fake metrics were found.

## Dashboard HTTP

Command checked `http://localhost:8501`.

Result: **failed**

Summary:

```text
URLError: [WinError 10061] connection refused
```

Interpretation: Streamlit was not running.
