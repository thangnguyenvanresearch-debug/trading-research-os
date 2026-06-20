# OpenBB Smoke Test Summary

## Result
OpenBB real-provider smoke test completed successfully.

## Environment
- Baseline Python: Python 3.12.10
- Isolated venv: `.venv-openbb`
- OpenBB installed: true
- OpenBB import OK: true
- OpenBB version attribute: unknown
- Extra venv runtime dependency installed: `PyYAML` so project config loading can run inside the isolated venv.

## Build Step
- `openbb-build` was run.
- First parallel import/build attempt caused a venv-local `.build.lock` conflict.
- Re-running `openbb-build` sequentially exited 0.
- Final OpenBB import succeeded.

## Ingestion Smoke Test
Command:

```bash
.\.venv-openbb\Scripts\python.exe scripts\ingest_openbb_data.py --symbols AAPL MSFT --asset-class equity --start-date 2022-01-01 --interval 1d
```

Result: passed.

- Provider used: `yfinance`
- Source: `openbb_adapter`
- Run ID: `openbb_a7c038f9422f`
- Status: `completed`
- Rows inserted: 2230
- Rows failed: 0
- Provider summary: `{'yfinance': {'symbols': ['AAPL', 'MSFT'], 'rows': 2230}}`
- Output file: `data/openbb/market_data/openbb_a7c038f9422f_equity_yfinance.csv`
- Parquet write failed because no parquet engine was installed in the venv; CSV fallback worked.

## DB Verification
Verified rows:

- AAPL / equity / yfinance / 1d: 1115 rows
- MSFT / equity / yfinance / 1d: 1115 rows

Verified ingestion run:

- `openbb_a7c038f9422f`: completed, rows_inserted=2230, rows_failed=0, warnings=[], errors=[]

## Dashboard Check
- `python -m compileall src/dashboard -q` was run inside `.venv-openbb` and passed.
- Streamlit server was not launched to avoid a long-running process.
- Dashboard code inspection from prior phase confirms the OpenBB page is DB-read-only and has no order controls/API key forms.

## Safety Confirmation
- Baseline compileall passed.
- Baseline pytest passed: 38 passed.
- Safe Freqtrade/sample workflow passed after OpenBB smoke test.
- Safety grep over `configs`, `src`, and `scripts` found no live/order enablement.
- Only safety grep hits were `secret/password` terms in the adapter's redaction regex.

Live trading, futures, leverage, and real orders remain disabled.
