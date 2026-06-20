# OpenBB Smoke Test Details

## Commands Run

### Baseline
```bash
python --version
python -m compileall src scripts -q
python -m pytest -q
```

Results:

- Python 3.12.10
- compileall passed
- pytest passed: `38 passed in 2.52s`

### Venv Creation And Install
```bash
python -m venv .venv-openbb
.\.venv-openbb\Scripts\python.exe -m pip install --upgrade pip
.\.venv-openbb\Scripts\pip.exe install openbb
.\.venv-openbb\Scripts\pip.exe install PyYAML
```

Results:

- venv created
- pip upgraded to 26.1.2
- OpenBB 4.7.2 installed successfully
- PyYAML installed to satisfy project config loading inside the venv

### OpenBB Import And Build
```bash
.\.venv-openbb\Scripts\python.exe -c "import importlib.util; print('openbb_installed=' + str(importlib.util.find_spec('openbb') is not None))"
.\.venv-openbb\Scripts\openbb-build.exe
.\.venv-openbb\Scripts\python.exe -c "import openbb; print('openbb_import_ok=True')"
```

Results:

- `openbb_installed=True`
- Initial parallel import/build caused a venv-local build lock conflict:
  - issue type: OpenBB build lock conflict
  - path type: venv package build lock
- Sequential `openbb-build` completed with exit code 0.
- Final OpenBB import succeeded.

### Database Init And Table Check
```bash
.\.venv-openbb\Scripts\python.exe scripts\init_database.py
```

OpenBB tables verified through SQLite fallback:

- `openbb_ingestion_runs`
- `openbb_macro_data`
- `openbb_market_data`
- `openbb_research_context`

DuckDB was not installed in the venv, so SQLite fallback was used.

### Real Provider Smoke Test
```bash
.\.venv-openbb\Scripts\python.exe scripts\ingest_openbb_data.py --symbols AAPL MSFT --asset-class equity --start-date 2022-01-01 --interval 1d
```

Output summary:

- `status=completed`
- `rows_inserted=2230`
- `rows_failed=0`
- provider: `yfinance`
- symbols: `AAPL`, `MSFT`
- output path: `data/openbb/market_data/openbb_a7c038f9422f_equity_yfinance.csv`

Warnings:

- Parquet write failed due missing parquet engine; CSV fallback succeeded.

Errors:

- None for ingestion.

### DB Verification
Market rows query returned:

- AAPL: 1115 rows
- MSFT: 1115 rows

Latest ingestion runs query returned:

- run_id `openbb_a7c038f9422f`
- status `completed`
- rows_inserted `2230`
- rows_failed `0`
- warnings_json `[]`
- errors_json `[]`

### Dashboard Compile Check
```bash
.\.venv-openbb\Scripts\python.exe -m compileall src\dashboard -q
```

Result: passed.

Streamlit was not launched.

### Safe Existing Workflow Regression
```bash
python scripts/init_database.py
python scripts/download_crypto_data.py --sample --pairs BTC/USDT ETH/USDT --timeframe 1h
python scripts/build_features.py
python scripts/generate_strategy_specs.py --asset-class crypto --count 3
python scripts/convert_specs_to_freqtrade.py
python scripts/run_freqtrade_backtests.py
python scripts/score_strategies.py --latest-only
```

Result: passed.

### Safety Grep
Searched over `configs`, `src`, and `scripts` for:

- `APPROVED_FOR_LIVE`
- `approved_for_live`
- `live_trading_enabled: true`
- `real_orders_enabled: true`
- `leverage_enabled: true`
- `futures_enabled: true`
- `create_order`
- `place_order`
- `market_order`
- `limit_order`
- `api_key`
- `secret`
- `private_key`
- `password`

Findings:

- No live/order enablement found.
- `secret/password` only appear in `src/data_brain/openbb_adapter.py` redaction regex.

## Source Patches
No source patches were made during this smoke test.

## Runtime Artifacts Created
- `.venv-openbb/`
- `data/openbb/market_data/openbb_a7c038f9422f_equity_yfinance.csv`
- Database rows in `openbb_market_data` and `openbb_ingestion_runs`
- `openbb_smoke_test_report/`

## Remaining Issues
1. Parquet output fell back to CSV because no parquet engine is installed in `.venv-openbb`.
   - Not fatal; CSV fallback is intended behavior.
   - Optional fix: install `pyarrow` in the OpenBB venv if Parquet output is required.

2. Dashboard was compile-checked but not visually launched.
   - Not fatal; no long-running Streamlit process was started.
   - Optional next step: launch dashboard manually and inspect page `10_openbb_ingestion`.

3. OpenBB import initially hit a build lock because import and build were run concurrently.
   - Resolved by sequential rerun.
   - No source impact.
