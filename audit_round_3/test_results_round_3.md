# Test Results Round 3

## Commands run

### 1. Python version

```text
python --version
Python 3.12.10
```

Result: pass.

### 2. Compile

```text
python -m compileall src scripts -q
```

Result: pass, no compile errors.

### 3. Pytest

```text
python -m pytest -q
...........................                                              [100%]
27 passed in 6.59s
```

Result: pass.

### 4. Safe fallback workflow

```text
python scripts/init_database.py
```

Result: pass. Output included:

```text
Initialized database at D:\AI2\QuantGit\trading-research-os\database\trading_os.duckdb
DuckDB is not available. Falling back to SQLite...
```

```text
python scripts/download_crypto_data.py --sample --pairs BTC/USDT ETH/USDT --timeframe 1h
```

Result: pass. Output included sample file paths and logs:

```text
Imported 720 candles for BTC/USDT 1h from sample_freqtrade_adapter
Imported 720 candles for ETH/USDT 1h from sample_freqtrade_adapter
```

```text
python scripts/build_features.py
```

Result: pass.

```text
Built 1838 feature rows.
```

```text
python scripts/generate_strategy_specs.py --asset-class crypto --count 3
```

Result: pass. Generated specs under `data/generated/specs`.

```text
python scripts/convert_specs_to_freqtrade.py
```

Result: pass. Generated strategies under `data/generated/freqtrade_strategies`.

```text
python scripts/run_freqtrade_backtests.py
```

Result: pass. Output:

```text
breakout_momentum_volume_v1: return=0.155 dd=0.001 trades=6
mean_reversion_bollinger_rsi_v1: return=-0.269 dd=0.269 trades=15
trend_pullback_rsi_atr_v1: return=-0.223 dd=0.223 trades=79
```

```text
python scripts/score_strategies.py
```

Result: pass. Output included `Risk reviews: 18` and per-symbol rejected decisions. Long output is expected because decisions/history are preserved across runs.

## Additional ad-hoc validation

Initial ad-hoc AST commands failed because `PYTHONPATH=src` was not set:

```text
ModuleNotFoundError: No module named 'core'
```

Rerun with `PYTHONPATH=src` passed:

```text
x=df.close.shift(periods=-1) -> has_risk True
x=df.close.shift(-3) -> has_risk True
x=df.iloc[index + n] -> has_risk True
x=df.close.shift(1) -> has_risk False
```

AST parse failure behavior:

```text
strict=True -> has_risk True, warning emitted
strict=False -> has_risk False, warning emitted
```

## Coverage observations

Tests cover:

- AST negative positional shift.
- AST future iloc.
- AST future-looking identifiers.
- Safe `shift(1)`, `rolling()`, `ewm()`.
- Risk gate rejects look-ahead review.
- SQLite fallback warning.
- Optional engine status `safe_for_live: false`.
- Optional engines missing do not crash.
- Full fallback pipeline.
- Safe defaults.

Minor gap: no dedicated pytest assertion for `shift(periods=-1)`, although ad-hoc validation confirms it works.

