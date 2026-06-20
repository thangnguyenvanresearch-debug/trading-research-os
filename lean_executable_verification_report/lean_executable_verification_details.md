# LEAN Executable Verification Details

## Current run resolution

No active LEAN/Python/Docker process was found after the interrupted second attempt. The latest run was already recorded in the database:

```text
run_id=lean_bt_f4d0947fa6ef
status=failed
```

Latest report:

```text
D:\AI2\QuantGit\trading-research-os\reports\lean\lean_bt_f4d0947fa6ef_equal_weight_demo.md
```

The report exists and records a timeout after 900 seconds.

## Commands run

### Docker

```powershell
docker --version
docker info
```

Initial result:

- `docker --version`: passed, Docker `29.2.0`
- `docker info`: passed initially

Later result:

- Docker daemon became unreachable:

```text
failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine
```

### LEAN CLI

```powershell
.\.venv-openbb\Scripts\lean.exe --version
```

Result:

```text
lean 1.0.225
```

### Project LEAN status

Before detection fix:

```text
lean_cli_available=false
```

After detection fix:

```text
lean_cli_available=true
lean_cli_path=D:\AI2\QuantGit\trading-research-os\.venv-openbb\Scripts\lean.exe
safe_for_live=false
```

## Compatibility fixes made

### Venv LEAN CLI detection

Updated:

- `src/lean_brain/lean_adapter.py`

The adapter now checks:

1. `shutil.which("lean")`
2. project-local `.venv-openbb\Scripts\lean.exe`

### Explicit LEAN CLI path

Updated:

- `src/lean_brain/lean_runner.py`

The runner now uses `status["lean_cli_path"]` when available.

### Local-only LEAN config

Updated:

- `src/lean_brain/lean_project_builder.py`

Generated project now includes:

- `lean.json`
- `config.json`

The generated `lean.json` contains:

- local data folder
- dummy local organization ids to satisfy local CLI config lookup
- `environment: backtesting`
- local/default data provider settings
- `live-mode: false`

It does not contain brokerage credentials, QuantConnect cloud credentials, API tokens, live mode, futures, leverage, or real-order settings.

### Tests

Updated:

- `tests/test_lean_adapter.py`
- `tests/test_lean_runner.py`

New coverage:

- detects project-local `.venv-openbb\Scripts\lean.exe`
- generated `lean.json` exists and has `live-mode=false`
- runner command includes `--lean-config`

## First executable attempt before fix

Run:

```powershell
.\.venv-openbb\Scripts\python.exe scripts\run_lean_backtest.py --symbols AAPL MSFT --provider yfinance --interval 1d --strategy-name equal_weight_demo
```

Recorded:

```text
run_id=lean_bt_588e60d6e28d
status=failed
```

Error:

```text
Error: This command requires a Lean configuration file, run `lean init` in an empty directory to create one, or specify the file to use with --lean-config
```

`lean init` was probed in a temp folder. It attempted a QuantConnect credential prompt and was aborted. No credentials were entered or stored.

## Second executable attempt after fix

Recorded:

```text
run_id=lean_bt_f4d0947fa6ef
status=failed
project_path=D:\AI2\QuantGit\trading-research-os\data\generated\lean\projects\equal_weight_demo_lean_5a615f2a482e
report_path=D:\AI2\QuantGit\trading-research-os\reports\lean\lean_bt_f4d0947fa6ef_equal_weight_demo.md
```

Command:

```text
D:\AI2\QuantGit\trading-research-os\.venv-openbb\Scripts\lean.exe backtest D:\AI2\QuantGit\trading-research-os\data\generated\lean\projects\equal_weight_demo_lean_5a615f2a482e --lean-config D:\AI2\QuantGit\trading-research-os\data\generated\lean\projects\equal_weight_demo_lean_5a615f2a482e\lean.json
```

Error:

```text
TimeoutExpired: Command ... timed out after 900 seconds
```

No metrics were parsed.

## DB verification

Latest LEAN runs include:

```text
lean_bt_f4d0947fa6ef failed
lean_bt_588e60d6e28d failed
```

Metrics query:

```text
Empty DataFrame
```

This is expected because no real LEAN result/statistics file was produced.

## Final validation

```powershell
.\.venv-openbb\Scripts\python.exe -m compileall src scripts -q
.\.venv-openbb\Scripts\python.exe -m compileall src\dashboard -q
.\.venv-openbb\Scripts\python.exe -m pytest -q
```

Result:

```text
104 passed in 17.49s
```

## Dashboard check

```powershell
.\.venv-openbb\Scripts\python.exe -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8501', timeout=10).status)"
```

Result:

```text
Connection refused
```

Interpretation:

- Streamlit was not running at the time of check.
- Source/page compile passed.
- Manual visual inspection required after launching dashboard.

## Safety grep

Search scope:

```text
configs src scripts tests README.md
```

No unsafe enablement found.

Observed hits were limited to:

- safety documentation
- false config flags
- tests asserting forbidden surfaces are absent
- Local AI denylist/redaction code
- LEAN research-only warnings
- `SetHoldings` inside generated local research/backtest skeleton

## Remaining issues

1. Executable LEAN backtest remains unverified.
2. Docker daemon became unreachable after the attempt.
3. The LEAN CLI command timed out after 900 seconds.
4. No metrics/result files were produced.

Next recommended work:

- Start Docker Desktop cleanly.
- Pre-pull/check LEAN Docker image separately if needed.
- Run a minimal LEAN sample project with the same local `lean.json`.
- Keep all cloud/login/broker/live settings disabled.

