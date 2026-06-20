# Test Results: LEAN Integration

## Commands

### Database init

```powershell
python scripts\init_database.py
```

Result: passed.

Output summary:

```text
Initialized database at D:\AI2\QuantGit\trading-research-os\database\trading_os.duckdb
DuckDB is not available. Falling back to SQLite...
```

### Compile

```powershell
python -m compileall src scripts -q
python -m compileall src\dashboard -q
```

Result: passed.

### Pytest

```powershell
python -m pytest -q
```

Result:

```text
102 passed in 18.20s
```

### LEAN skip-run smoke

```powershell
python scripts\run_lean_backtest.py --symbols AAPL MSFT --provider yfinance --interval 1d --strategy-name equal_weight_demo --skip-run
```

Result:

```text
run_id=lean_bt_f2d6b4617f0d
status=skeleton_created
project_path=D:\AI2\QuantGit\trading-research-os\data\generated\lean\projects\equal_weight_demo_lean_6581bd3cd48e
report_path=D:\AI2\QuantGit\trading-research-os\reports\lean\lean_bt_f2d6b4617f0d_equal_weight_demo.md
warnings=["LEAN run skipped by request; research-only skeleton was created."]
errors=[]
```

### LEAN unavailable smoke

```powershell
python scripts\run_lean_backtest.py --symbols AAPL MSFT --provider yfinance --interval 1d --strategy-name equal_weight_demo
```

Result:

```text
run_id=lean_bt_a0e709b0ac00
status=unavailable
project_path=D:\AI2\QuantGit\trading-research-os\data\generated\lean\projects\equal_weight_demo_lean_a7985c5f7230
report_path=D:\AI2\QuantGit\trading-research-os\reports\lean\lean_bt_a0e709b0ac00_equal_weight_demo.md
warnings=["LEAN CLI is not installed; only data export and research skeleton generation are available."]
errors=[]
```

### DB verification

Latest LEAN runs exist:

```text
lean_bt_f2d6b4617f0d skeleton_created
lean_bt_a0e709b0ac00 unavailable
```

Metrics table:

```text
Empty DataFrame
```

Expected because LEAN CLI is unavailable and no result JSON exists.

### CSV verification

```text
AAPL_yfinance_1d.csv 1115 rows, 1115 unique timestamps, 0 duplicate timestamps
MSFT_yfinance_1d.csv 1115 rows, 1115 unique timestamps, 0 duplicate timestamps
```

### Dashboard HTTP

```powershell
python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8501', timeout=10).status)"
```

Result:

```text
200
```

