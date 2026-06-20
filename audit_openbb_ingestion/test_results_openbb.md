# Test Results OpenBB

## Compile
Command: `python -m compileall src scripts -q`

Result: passed.

## Pytest
Command: `python -m pytest -q`

Result: passed.

Summary: `36 passed in 8.01s`.

## OpenBB Installation Check
Command: `python -c "import importlib.util; print('openbb_installed=' + str(importlib.util.find_spec('openbb') is not None))"`

Result: `openbb_installed=False`.

## Safe Freqtrade/Sample Workflow
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

Observed:

- Database initialized.
- Sample BTC/USDT and ETH/USDT data generated/imported.
- 1850 feature rows built in this run.
- 3 YAML specs generated.
- 3 Freqtrade-compatible strategies generated.
- Internal fallback backtests completed.
- Latest-only score output printed 3 rejected decisions for one latest run.

## OpenBB Missing-Package CLI
Command:

```bash
python scripts/ingest_openbb_data.py --symbols AAPL MSFT --asset-class equity --start-date 2022-01-01 --interval 1d
```

Result: passed, exit 0.

Output summary:

- Printed clear missing-package message.
- Did not crash.
- Did not create fake OpenBB data.

Post-command local DB counts:

- `openbb_market_data=0`
- `openbb_macro_data=0`
- `openbb_ingestion_runs=0`

## Command Failures
None.
