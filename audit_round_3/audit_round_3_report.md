# Audit Round 3 Report

## Scope

Audit này tập trung vào Round 3 remediation, không re-audit toàn bộ dự án từ đầu. Các khu vực kiểm tra:

- Safety invariants.
- AST-based look-ahead detection.
- Risk gate integration.
- SQLite fallback warning.
- Optional engine diagnostics.
- Dashboard honesty.
- README accuracy.
- Test quality.
- Compile và safe fallback workflow.
- Regression risk.

Chỉ đọc source và chạy lệnh safe. Không chạy real exchange-connected Freqtrade download, Hummingbot live bot, Nautilus live execution, hoặc bất kỳ lệnh đặt lệnh nào.

## Commands run

### Required checks

- `python --version`: pass, Python 3.12.10.
- `python -m compileall src scripts -q`: pass.
- `python -m pytest -q`: pass, `27 passed in 6.59s`.

### Safe fallback workflow

All passed:

- `python scripts/init_database.py`
- `python scripts/download_crypto_data.py --sample --pairs BTC/USDT ETH/USDT --timeframe 1h`
- `python scripts/build_features.py`
- `python scripts/generate_strategy_specs.py --asset-class crypto --count 3`
- `python scripts/convert_specs_to_freqtrade.py`
- `python scripts/run_freqtrade_backtests.py`
- `python scripts/score_strategies.py`

SQLite fallback warning appeared clearly once per process because DuckDB is unavailable in this environment.

### Failed ad-hoc commands

Two initial ad-hoc AST commands failed due missing `PYTHONPATH=src`:

```text
ModuleNotFoundError: No module named 'core'
```

They were rerun successfully with `PYTHONPATH=src`.

## 1. Safety invariant audit

### Result

Fixed / safe.

### Evidence

- `configs/global.yaml` has:
  - `live_trading_enabled: false`
  - `real_orders_enabled: false`
  - `leverage_enabled: false`
  - `futures_enabled: false`
- `.env.example` has:
  - `ENABLE_LIVE_TRADING=false`
  - `ENABLE_FUTURES=false`
  - `ENABLE_LEVERAGE=false`
- Static grep for dangerous terms found only README line saying there is no `APPROVED_FOR_LIVE`.
- No `create_order`, `place_order`, `market_order`, `limit_order`, `api_key`, `secret`, `private_key`, or `password` issue found in scanned source/config/README/scripts.
- Optional engine status factory hardcodes `safe_for_live: False`.

### Assessment

No Round 3 change added trading execution capability. No API key input or secret handling was added.

## 2. AST look-ahead audit

### Result

Fixed.

### Evidence

`src/core/validation.py`:

- imports `ast`.
- keeps `FORBIDDEN_STRINGS`.
- defines `analyze_python_lookahead_risk(source_code, strict=True)`.
- returns `has_risk`, `warnings`, `risk_patterns`.
- does not execute code.
- does not import generated strategy modules.

Detected by tests or ad-hoc command:

- `df["close"].shift(-1)`: detected.
- `df.close.shift(-2)`: detected.
- `shift(periods=-1)`: detected by ad-hoc command.
- `df.iloc[i + 1)`: equivalent test uses `dataframe.iloc[i + 1]`, detected.
- `dataframe.iloc[index + n]`: detected.
- `future_close` and `next_candle`: detected.
- safe `shift(1)`, `rolling()`, `ewm()`: not flagged.

Parse failure behavior:

- `strict=True`: `has_risk: True`.
- `strict=False`: warning returned, no hard risk.

### Limitation

This is still static heuristic analysis, not full data-flow analysis. It does not prove absence of all look-ahead leaks.

## 3. Risk gate integration audit

### Result

Fixed with minor diagnostic gap.

### Evidence

`src/risk_brain/risk_gate.py`:

- imports `analyze_python_lookahead_risk` and `contains_forbidden_logic`.
- `_lookahead_review()` reads source YAML and generated strategy code.
- It collects `spec_path` and generated `code_path` into `inspected_paths`.
- It runs substring scan and AST scan.
- `review_metrics()` rejects if `lookahead_review.has_lookahead_risk` is true.

Round 2 behavior preserved:

- dry-run divergence check remains.
- archived status remains.
- approved_for_dry_run promotion remains.
- weak metrics rejection remains.
- no live approval status exists.

### Minor gap

`inspected_paths` are returned by `_lookahead_review()`, but not stored into `risk_reviews.flags`. This does not break safety but makes dashboard/debug less direct if look-ahead fires.

## 4. SQLite fallback warning audit

### Result

Fixed.

### Evidence

`src/core/database.py`:

- `SQLITE_FALLBACK_WARNING` clearly says DuckDB unavailable and gives install command `pip install -e .[database]`.
- `_warn_sqlite_fallback_once()` uses project logger.
- `connect()` calls `_warn_sqlite_fallback_once()` before SQLite fallback.
- Test `tests/test_database_fallback.py` monkeypatches `duckdb=None`, initializes DB, fetches data, and asserts one warning.
- Safe workflow output showed warning once in each process.

### Assessment

Fallback remains functional. Warning does not print secrets or sensitive config values.

## 5. Optional engine status audit

### Result

Fixed / mostly fixed.

### Evidence

`src/core/engine_status.py` defines a standard shape:

- `engine`
- `installed`
- `status`
- `role`
- `current_capability`
- `next_step`
- `safe_for_live`

Status functions:

- `get_openbb_status()`
- `get_qlib_status()`
- `get_lean_status()`
- `get_hummingbot_status()`
- `get_nautilus_status()`

All return `safe_for_live: false`.

No adapter claims ready:

- OpenBB: `scaffold_only`.
- Qlib: `scaffold_only`.
- LEAN: `scaffold_only`.
- Hummingbot: `partial`.
- Nautilus: `scaffold_only`.

FinceptTerminal is not falsely presented as implemented. It remains `mentioned only / future` in README and `mentioned_only` in config.

### Minor taxonomy gap

`configs/engine_registry.yaml` uses `status: mentioned_only` for FinceptTerminal, while code-level `ALLOWED_ENGINE_STATUSES` does not include `mentioned_only`. Since Fincept has no adapter and is honestly documented, this is low severity.

## 6. Dashboard diagnostics audit

### Result

Fixed.

### Evidence

`src/dashboard/streamlit_app.py` displays status objects for:

- Freqtrade.
- OpenBB.
- LEAN.
- Qlib.
- Hummingbot.
- Nautilus.

Pages:

- `06_equity_lean_qlib.py` displays LEAN/Qlib statuses.
- `07_market_making_lab.py` displays Hummingbot status and says paper-only/no live market making.
- `09_nautilus_future_engine.py` displays Nautilus status and v2 migration note.

Static search found no live trading button, API key form, subprocess bot launch, or order placement control.

## 7. README audit

### Result

Fixed.

README states:

- Round 3 added AST static look-ahead checks.
- SQLite fallback warning exists.
- Optional engine diagnostics standardized.
- Live trading/futures/leverage/real orders remain disabled.
- Freqtrade remains v1 working path.
- OpenBB/Qlib/LEAN/Nautilus/FinceptTerminal remain scaffold/future.
- Hummingbot remains paper/scanner lab.
- Sample/fallback/backtest limitations remain clear.

No exaggerated production-ready claim found.

## 8. Test audit

### Result

Pass with minor coverage gap.

Pytest result:

```text
27 passed in 6.59s
```

Meaningful coverage includes:

- AST negative shift.
- AST future iloc.
- Future-looking identifiers.
- Safe shift/rolling/ewm.
- Risk gate look-ahead rejection.
- SQLite fallback warning.
- Optional engine status safe_for_live false.
- Optional engines missing do not crash.
- Full fallback pipeline.
- Safe defaults.

Minor gap:

- No pytest case for `shift(periods=-1)`, though ad-hoc command verified it is detected.

## 9. Regression audit

### Result

Không phát hiện regression.

Validated:

- sample data workflow.
- generated specs.
- generated Freqtrade strategy conversion.
- internal fallback backtest.
- scoring/risk review.
- tests and compile.
- safety grep.

## Remaining risks

- Optional engines outside Freqtrade are still scaffold/future by design.
- AST look-ahead detection is a heuristic, not formal proof.
- Risk review flags do not persist inspected file paths yet.
- FinceptTerminal status taxonomy not fully aligned with code-level status enum.

## Final verdict

Round 3 remediation is accepted. Project remains safe for local research/demo and is more transparent than Round 2.

