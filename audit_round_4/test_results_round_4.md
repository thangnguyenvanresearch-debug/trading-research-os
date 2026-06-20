# Test Results Round 4

## Python
Command: `python --version`

Result: Python 3.12.10.

## Compile
Command: `python -m compileall src scripts -q`

Result: passed. No compile errors.

## Pytest
Command: `python -m pytest -q`

Result: passed.

Summary: `29 passed in 2.04s`.

## Safety Search
Searched safely for:

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

Executable source/config/script scope had no live/order/secret hits. Test hits for `APPROVED_FOR_LIVE` are safety assertions that it does not exist.

## Safe Fallback Workflow
Commands run:

1. `python scripts/init_database.py`
   - Passed.
   - DuckDB unavailable warning emitted; SQLite fallback worked.

2. `python scripts/download_crypto_data.py --sample --pairs BTC/USDT ETH/USDT --timeframe 1h`
   - Passed.
   - Generated/imported 720 candles for BTC/USDT and 720 candles for ETH/USDT.
   - Source label: `sample_freqtrade_adapter`.

3. `python scripts/build_features.py`
   - Passed.
   - Built 1840 feature rows.

4. `python scripts/generate_strategy_specs.py --asset-class crypto --count 3`
   - Passed.
   - Generated 3 YAML specs under `data/generated/specs`.

5. `python scripts/convert_specs_to_freqtrade.py`
   - Passed.
   - Generated 3 strategy files under `data/generated/freqtrade_strategies`.

6. `python scripts/run_freqtrade_backtests.py`
   - Passed.
   - Internal fallback backtest produced metrics for 3 strategies.

7. `python scripts/score_strategies.py`
   - Passed.
   - Risk reviews and decisions produced; sample/fallback strategies were rejected.

## Command Failures
None during Round 4 audit commands.
