# Dashboard Smoke Details

## Commands run

Baseline:

```powershell
python --version
python -m compileall src scripts -q
python -m pytest -q
python -c "import importlib.util; print('streamlit_installed=' + str(importlib.util.find_spec('streamlit') is not None))"
```

Results:

- Python: `3.12.10`
- Compileall: passed
- Pytest: `44 passed in 2.57s`
- Base environment Streamlit: installed

OpenBB venv check:

```powershell
.\.venv-openbb\Scripts\python.exe -c "import importlib.util; print('streamlit_installed=' + str(importlib.util.find_spec('streamlit') is not None)); print('openbb_installed=' + str(importlib.util.find_spec('openbb') is not None))"
```

Initial result:

- `streamlit_installed=False`
- `openbb_installed=True`

Fix applied:

```powershell
.\.venv-openbb\Scripts\python.exe -m pip install streamlit
```

Post-install result:

- `streamlit_installed=True`
- `openbb_installed=True`

Dashboard launch:

```powershell
.\.venv-openbb\Scripts\python.exe -m streamlit run src/dashboard/streamlit_app.py --server.port 8501 --server.address localhost --server.headless true --browser.gatherUsageStats false
```

Started as background process with stdout/stderr logs:

- PID: `624`
- stdout log: `dashboard_smoke_streamlit.out.log`
- stderr log: `dashboard_smoke_streamlit.err.log`

HTTP checks:

```powershell
python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8501', timeout=10).status)"
python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8501/_stcore/health', timeout=10).read().decode())"
```

Results:

- Root URL status: `200`
- Health endpoint: `ok`

Dashboard compile check:

```powershell
python -m compileall src/dashboard -q
```

Result: passed.

Safe workflow regression:

```powershell
python scripts/init_database.py
python scripts/download_crypto_data.py --sample --pairs BTC/USDT ETH/USDT --timeframe 1h
python scripts/build_features.py
python scripts/generate_strategy_specs.py --asset-class crypto --count 3
python scripts/convert_specs_to_freqtrade.py
python scripts/run_freqtrade_backtests.py
python scripts/score_strategies.py --latest-only
```

Results:

- Database init: passed, with expected DuckDB-to-SQLite fallback warning in base environment.
- Sample data download: passed.
- Feature build: `1852 feature rows`.
- Spec generation: 3 specs generated.
- Freqtrade strategy conversion: 3 generated strategy files.
- Internal fallback backtests: passed.
- Scoring: passed, `3` latest decisions printed, all rejected due to risk flags.

OpenBB DB verification:

```powershell
$env:PYTHONPATH='src'
python -c 'from core.database import initialize_database, fetch_dataframe; initialize_database(); print(fetch_dataframe("SELECT symbol, provider, interval, COUNT(*) AS rows FROM openbb_market_data GROUP BY symbol, provider, interval ORDER BY symbol"))'
```

Result:

| symbol | provider | interval | rows |
|---|---|---:|---:|
| AAPL | yfinance | 1d | 1115 |
| MSFT | yfinance | 1d | 1115 |

Safety grep:

```powershell
rg -n --hidden --glob '!data/**' --glob '!reports/**' --glob '!database/**' "APPROVED_FOR_LIVE|approved_for_live|live_trading_enabled:\s*true|real_orders_enabled:\s*true|leverage_enabled:\s*true|futures_enabled:\s*true|create_order|place_order|market_order|limit_order|api_key|secret|private_key|password" configs src scripts
```

Result:

- One hit in `src/data_brain/openbb_adapter.py`: secret-redaction regex pattern.
- No actual secret value printed.
- No live/order enablement found.

## Notes

Visual browser automation was not available because Playwright is not installed in the local Node REPL environment. No additional visual testing package was installed. Verification used Streamlit process status, HTTP status, health endpoint, static source inspection of `src/dashboard/pages/10_openbb_ingestion.py`, dashboard compile, and local DB checks.

To open manually, use:

```text
http://localhost:8501
```

If the browser still shows refused, refresh once and confirm process PID `624` is still running. To stop it later:

```powershell
Stop-Process -Id 624
```
