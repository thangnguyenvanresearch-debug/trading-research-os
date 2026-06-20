# File-level Findings Round 3

## `src/core/validation.py`

- Status: fixed.
- Evidence: imports `ast`; defines `analyze_python_lookahead_risk(source_code, strict=True)` returning `has_risk`, `warnings`, `risk_patterns`.
- Detects:
  - `.shift(-1)` and `.shift(-2)` through AST call analysis.
  - `.shift(periods=-1)` through keyword arg check.
  - `.iloc[i + 1]` and `.iloc[index + n]` through AST subscript/binop analysis.
  - future-looking identifiers such as `future_close`, `future_return`, `next_candle`, `tomorrow`, `lookahead`.
- Safe behavior:
  - Does not execute code.
  - Does not dynamically import generated strategy files.
  - `strict=True` parse failure returns `has_risk: True`.
  - `strict=False` parse failure returns warning without hard fail.
- Minor limitation: heuristic does not perform full data-flow analysis, e.g. if a variable is assigned `-1` elsewhere and later passed to `.shift(periods=n)`, this is not resolved.

## `src/risk_brain/risk_gate.py`

- Status: fixed with minor diagnostic gap.
- Evidence: imports `analyze_python_lookahead_risk` and `contains_forbidden_logic`.
- `_lookahead_review()` reads `strategy_specs.source_yaml`, `strategy_specs.spec_path`, and `generated_strategies.code_path`.
- For existing generated code paths, it runs substring scan plus AST scan.
- It returns `has_lookahead_risk`, `issues`, `warnings`, and `inspected_paths`.
- `review_metrics()` rejects when `lookahead_review.has_lookahead_risk` is true.
- Round 2 behavior preserved: dry-run divergence, archived, approved_for_dry_run, weak metrics rejection.
- Minor gap: `inspected_paths` are returned by the hook but not persisted into `risk_reviews.flags`.

## `src/core/database.py`

- Status: fixed.
- Evidence: defines `SQLITE_FALLBACK_WARNING` with clear DuckDB install instruction.
- `_warn_sqlite_fallback_once()` logs warning once per process.
- `connect()` uses DuckDB when available, otherwise warns and opens SQLite.
- If DuckDB connection fails, code logs a warning and downgrades to SQLite.
- Test `tests/test_database_fallback.py` monkeypatches `duckdb=None` and verifies one warning.
- No secrets/config values are printed.

## `src/core/engine_status.py`

- Status: fixed.
- Evidence: defines `OptionalEngineStatus`, `EngineStatusValue`, `ALLOWED_ENGINE_STATUSES`, and `optional_engine_status()`.
- Status shape includes: `engine`, `installed`, `status`, `role`, `current_capability`, `next_step`, `safe_for_live`.
- `safe_for_live` is hardcoded false by factory.

## `src/data_brain/openbb_adapter.py`

- Status: fixed for diagnostics; scaffold remains.
- Evidence: `get_openbb_status()` returns standardized status with `status="scaffold_only"` and `safe_for_live=false`.
- Adapter remains non-execution and only placeholder context.

## `src/qlib_brain/qlib_experiment_runner.py`

- Status: fixed for diagnostics; scaffold remains.
- Evidence: `get_qlib_status()` returns `scaffold_only`, current capability, next step, and `safe_for_live=false`.
- No ML experiment integration is implemented in Round 3, which matches scope.

## `src/lean_brain/lean_backtest_runner.py`

- Status: fixed for diagnostics; scaffold remains.
- Evidence: `get_lean_status()` returns `scaffold_only`, CLI availability role, next step, and `safe_for_live=false`.
- LEAN backtest execution remains future work.

## `src/hummingbot_brain/spread_scanner.py`

- Status: fixed for diagnostics; partial paper/scanner remains.
- Evidence: `get_hummingbot_status()` returns `partial`, paper/scanner role, current local spread/inventory/arbitrage capability, and `safe_for_live=false`.
- No live market making added.

## `src/nautilus_brain/nautilus_adapter.py`

- Status: fixed for diagnostics; scaffold remains.
- Evidence: `get_nautilus_status()` returns `scaffold_only`, future v2 role, next step, and `safe_for_live=false`.
- Existing `nautilus_status()` also reports `live_enabled: False`.

## `configs/engine_registry.yaml`

- Status: mostly fixed.
- Evidence: engine entries now include `status` and `safe_for_live: false`.
- OpenBB/Qlib/LEAN/Nautilus are `scaffold_only`; Freqtrade/Hummingbot are `partial`.
- Minor taxonomy gap: FinceptTerminal uses `status: mentioned_only`, which is honest but not in `ALLOWED_ENGINE_STATUSES`.

## `src/dashboard/streamlit_app.py`

- Status: fixed.
- Evidence: dashboard constructs statuses for Freqtrade plus `get_openbb_status()`, `get_lean_status()`, `get_qlib_status()`, `get_hummingbot_status()`, `get_nautilus_status()`.
- Displays installed/status/role/capability/next_step/safe_for_live through dataframe.
- Static search found no live trading controls, API key forms, order placement functions, or subprocess bot launch.

## `src/dashboard/pages/06_equity_lean_qlib.py`

- Status: fixed.
- Evidence: displays `[get_lean_status(), get_qlib_status()]`.
- Still clearly states Phase 3 future work.

## `src/dashboard/pages/07_market_making_lab.py`

- Status: fixed.
- Evidence: displays `get_hummingbot_status()` and caption says paper-only/no live market making.
- No live bot launch found.

## `src/dashboard/pages/09_nautilus_future_engine.py`

- Status: fixed.
- Evidence: displays `get_nautilus_status()` and page copy identifies Phase 5 migration target.
- No live Nautilus execution added.

## `README.md`

- Status: fixed.
- Evidence: includes Round 3 Hardening section: AST checks, SQLite fallback warning, standardized optional diagnostics, disabled live/futures/leverage/orders.
- Engine table remains transparent: OpenBB/Qlib/LEAN/Nautilus scaffold/future; Freqtrade v1 focus; Hummingbot partial paper/scanner; FinceptTerminal mentioned/future.
- Limitations still warn about sample/fallback/backtest overfitting.

## `tests/test_no_lookahead.py`

- Status: mostly fixed.
- Evidence: tests negative shift, future iloc, future variable names, safe past-only indicators.
- Gap: no pytest case for `shift(periods=-1)`, though ad-hoc command confirms analyzer catches it.

## `tests/test_risk_gate.py`

- Status: fixed.
- Evidence: tests weak strategy rejection, dry-run divergence, AST-derived lookahead rejection, approved_for_dry_run, archived.

## `tests/test_database_fallback.py`

- Status: fixed.
- Evidence: monkeypatches `database.duckdb=None`, confirms fallback warning appears once while DB initializer/fetch works.

## `tests/test_optional_engines.py`

- Status: fixed.
- Evidence: verifies optional engine missing behavior does not crash and standardized statuses have allowed values and `safe_for_live is False`.

