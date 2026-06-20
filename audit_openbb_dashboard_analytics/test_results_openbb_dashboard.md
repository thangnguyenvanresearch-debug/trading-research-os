# Test Results OpenBB Dashboard Analytics

## Pytest
Command:

```bash
python -m pytest -q
```

Result: passed.

Summary: `44 passed in 2.42s`.

## Compile
Commands:

```bash
python -m compileall src scripts -q
python -m compileall src/dashboard -q
```

Result: both passed.

## CLI Analytics Smoke Test
Command:

```bash
python scripts/report_openbb_analytics.py --symbols AAPL MSFT --provider yfinance --interval 1d
```

Result: passed.

Observed:

- AAPL: 1115 rows.
- MSFT: 1115 rows.
- Data quality: duplicates=0, missing_close=0, non_positive_prices=0, high_below_low=0.
- CSV report exists: `reports/openbb/openbb_summary.csv`.

## Safe Existing Workflow
Command chain:

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

## Safety Grep
No live/order enablement found.

Hits:

- `src/data_brain/openbb_adapter.py`: `secret/password` in redaction regex only.
- tests: order function names and `APPROVED_FOR_LIVE` only in absence/safety assertions.

## Visual Dashboard
Visual dashboard launch not verified.
