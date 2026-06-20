# Test Results - Qlib Integration

## Database Init

Command:

```powershell
python scripts\init_database.py
```

Result: **passed**

Output summary:

```text
Initialized database at D:\AI2\QuantGit\trading-research-os\database\trading_os.duckdb
DuckDB is not available. Falling back to SQLite...
```

## Compile

Command:

```powershell
python -m compileall src scripts -q
```

Result: **passed**

Command:

```powershell
python -m compileall src\dashboard -q
```

Result: **passed**

## Pytest

Command:

```powershell
python -m pytest -q
```

Result:

```text
120 passed in 19.65s
```

## Qlib Availability

Command:

```powershell
python -c "import importlib.util; print('qlib_installed=' + str(importlib.util.find_spec('qlib') is not None))"
```

Result:

```text
qlib_installed=False
```

## Skip-run Smoke

Command:

```powershell
python scripts\run_qlib_experiment.py --symbols AAPL MSFT --provider yfinance --interval 1d --experiment-name qlib_demo --skip-run
```

Result:

```text
run_id=qlib_run_3ac2315d99a8
status=dataset_exported
dataset_export_id=qlib_export_182f756b2b6a
metrics_count=0
predictions_count=0
errors=[]
```

## Normal Unavailable Smoke

Command:

```powershell
python scripts\run_qlib_experiment.py --symbols AAPL MSFT --provider yfinance --interval 1d --experiment-name qlib_demo
```

Result:

```text
run_id=qlib_run_045090f920b8
status=unavailable
dataset_export_id=qlib_export_b9c5625b0de2
metrics_count=0
predictions_count=0
warnings=["Qlib is not installed; dataset export works, but Qlib execution is unavailable."]
errors=[]
```

## Dataset Verification

Latest dataset:

- path: `data/generated/qlib/datasets/qlib_export_b9c5625b0de2/features.csv`
- shape: `(2220, 13)`
- symbols: `AAPL`, `MSFT`
- duplicate `symbol+timestamp`: `0`
- label column present: `true`
- manifest rows: `2220`
- missing label count: `0`

## Dashboard HTTP

Result:

```text
URLError: [WinError 10061] connection refused
```

Streamlit was not running. Source compile passed.
