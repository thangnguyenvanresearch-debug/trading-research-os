# Audit OpenBB Ingestion Report

## Scope
Audit kiểm tra phase OpenBB ingestion sau khi project thêm các file:

- `configs/openbb.yaml`
- `configs/engine_registry.yaml`
- `database/schema.sql`
- `src/data_brain/openbb_adapter.py`
- `scripts/ingest_openbb_data.py`
- `src/dashboard/pages/10_openbb_ingestion.py`
- `src/feature_brain/openbb_feature_bridge.py`
- `tests/test_openbb_adapter.py`
- `README.md`

Không sửa source code. Chỉ ghi file audit trong `audit_openbb_ingestion`.

## Commands Run
- `python -m compileall src scripts -q`: passed.
- `python -m pytest -q`: `36 passed in 8.01s`.
- `python -c "import importlib.util; ..."`: `openbb_installed=False`.
- Safe workflow:
  - `python scripts/init_database.py`: passed.
  - `python scripts/download_crypto_data.py --sample --pairs BTC/USDT ETH/USDT --timeframe 1h`: passed.
  - `python scripts/build_features.py`: passed, built 1850 feature rows in this run.
  - `python scripts/generate_strategy_specs.py --asset-class crypto --count 3`: passed.
  - `python scripts/convert_specs_to_freqtrade.py`: passed.
  - `python scripts/run_freqtrade_backtests.py`: passed.
  - `python scripts/score_strategies.py --latest-only`: passed, printed 3 latest-run decisions.
- `python scripts/ingest_openbb_data.py --symbols AAPL MSFT --asset-class equity --start-date 2022-01-01 --interval 1d`: passed, printed missing-package message and exited 0.
- DB check after missing-package CLI: `openbb_market_data=0`, `openbb_macro_data=0`, `openbb_ingestion_runs=0`.

DuckDB is not installed/available in this environment, so SQLite fallback warning appeared. SQLite path worked. DuckDB execution for the new OpenBB schema: Không xác minh được.

## 1. Safety Audit
Evidence:

- `configs/global.yaml` still has:
  - `live_trading_enabled: false`
  - `real_orders_enabled: false`
  - `leverage_enabled: false`
  - `futures_enabled: false`
- `scripts/ingest_openbb_data.py` imports `_bootstrap`, and `scripts/_bootstrap.py` calls `assert_research_only(load_global_config())`.
- Search results:
  - `APPROVED_FOR_LIVE` appears in README/tests as a forbidden/absent permission, not as implementation.
  - `create_order/place_order/market_order/limit_order` appear only in tests asserting such names are absent.
  - `secret/password` appear in `src/data_brain/openbb_adapter.py` only in error redaction regex.
- No API key forms, real exchange configs, or order-placement paths were found.

Status: implemented / safe.

## 2. OpenBB Config Audit
Files inspected:

- `configs/openbb.yaml`
- `configs/engine_registry.yaml`

Findings:

- `safe_mode: true`: implemented.
- `allow_credentials: false`: implemented.
- `write_to_database: true`: implemented.
- `write_to_parquet: true`: implemented.
- Provider priority exists for equity, crypto, ETF, macro.
- Default universe exists for equities, ETFs, crypto.
- `engine_registry.yaml` marks OpenBB as `partial`, not `scaffold_only`.
- `safe_for_live: false` and `execution_allowed: false` are present.

Status: implemented.

Caveat: provider priority is configured, but real provider execution cannot be verified without OpenBB installed.

## 3. Database Schema Audit
Files inspected:

- `database/schema.sql`
- `src/core/database.py`

Required tables exist:

- `openbb_market_data`: implemented.
- `openbb_macro_data`: implemented.
- `openbb_ingestion_runs`: implemented.
- `openbb_research_context`: implemented.

SQLite verification:

- `python scripts/init_database.py` passed.
- Query counts against OpenBB tables succeeded.

DuckDB verification:

- Không xác minh được because DuckDB is unavailable in this environment.
- SQL uses portable `TEXT`, `REAL`, `INTEGER` and `CREATE TABLE IF NOT EXISTS`, so it is likely compatible, but not runtime-verified.

Older DB migration:

- `initialize_database()` runs the full schema, so new OpenBB tables are created for existing DB files.
- `_ensure_runtime_columns()` remains focused on older v1 runtime columns. No OpenBB column migration issue observed.

Status: implemented for SQLite; DuckDB not verifiable.

## 4. OpenBB Adapter Audit
File inspected:

- `src/data_brain/openbb_adapter.py`

Implemented:

- `detect_openbb()` safely checks package availability with `importlib.util.find_spec`.
- `get_openbb_status()` returns standardized optional engine status and `safe_for_live: false` through `optional_engine_status()`.
- `OpenBBIngestionResult` dataclass exists with run_id, status, rows_inserted, rows_failed, warnings, errors, provider_summary, output_paths.
- `ingest_openbb_market_data()` exists and accepts symbols, asset_class, date range, interval, provider, DB/file write flags, and an injectable fetcher for tests.
- Normalization includes required fields:
  - symbol
  - asset_class
  - provider
  - interval
  - timestamp
  - open/high/low/close/volume
  - adjusted_close
  - source
  - retrieved_at
  - metadata_json
- One failed symbol does not fail whole run; errors are collected per symbol.
- File output uses `data/openbb/market_data` and `data/openbb/macro_data`.
- Parquet failure falls back to CSV.
- Macro ingestion is best-effort and warns about provider/credential availability.
- Error text has credential-like redaction regex.
- No live trading or order placement functions exist.

Not verifiable:

- Real OpenBB endpoint compatibility, because OpenBB is not installed.
- Real provider schemas and credential behavior.

Minor issues:

- `openbb_adapter.py` is now large and combines detection, fetching, normalization, DB writing, file writing, and context summaries. It is acceptable for this phase, but should be split later if provider support grows.
- `_timestamp_series()` falls back to RangeIndex strings when no timestamp/date column exists. This prevents crashes but may create weak timestamps for malformed provider output. Should be flagged as warning in a future hardening pass.

Status: partially implemented, safe.

## 5. CLI Audit
File inspected:

- `scripts/ingest_openbb_data.py`

Findings:

- Uses `_bootstrap`, which calls `assert_research_only()`.
- Handles missing OpenBB package gracefully: prints clear message and exits 0 unless `--strict` is used.
- Supports symbols, asset class, start date, end date, interval, provider, macro indicators, sample context, write flags, strict mode.
- Does not require credentials.
- Does not run live trading.
- Does not create fake data when OpenBB is missing.

Status: implemented.

## 6. Dashboard Audit
Files inspected:

- `src/dashboard/pages/10_openbb_ingestion.py`
- `src/dashboard/streamlit_app.py`

Findings:

- OpenBB page calls `initialize_database()` and reads existing DB tables.
- It does not trigger external OpenBB fetch on page load.
- It shows OpenBB status, ingestion runs, market data preview, macro data preview, warnings/errors columns from ingestion runs.
- It has no live trading buttons, API key forms, or order controls.
- Since it initializes DB first, missing OpenBB tables should be created before queries.

Status: implemented / safe.

## 7. Feature Bridge Audit
File inspected:

- `src/feature_brain/openbb_feature_bridge.py`

Findings:

- Bridge only reads local DB and does not call OpenBB or external providers.
- It converts `interval` to `timeframe` and returns common OHLCV feature input columns.
- It does not force Freqtrade pipeline to depend on OpenBB.
- Empty DataFrame is handled.

Issue:

- If callers use the bridge before `initialize_database()` has created `openbb_market_data`, `fetch_dataframe()` may raise missing-table DB errors. This is low priority because normal CLI/dashboard paths initialize DB, but the bridge itself is not fully defensive.

Status: partially implemented.

## 8. Tests Audit
File inspected:

- `tests/test_openbb_adapter.py`

Run result: `36 passed`.

Covered:

- OpenBB missing status.
- Normalization required columns.
- One-symbol failure behavior.
- No live capability/order function names.
- CLI missing-package path.

Tests do not require internet and do not require OpenBB installed.

Status: implemented.

## 9. Compile Audit
`python -m compileall src scripts -q` passed.

Status: implemented.

## 10. Safe Workflow Audit
Safe Freqtrade/sample workflow passed. OpenBB changes did not break v1 crypto fallback pipeline.

Status: implemented.

## 11. OpenBB Missing-Package CLI Audit
Command passed with clear output:

`OpenBB is not installed. Install optional OpenBB support or keep using Freqtrade/sample workflow.`

Post-command DB counts:

- `openbb_market_data=0`
- `openbb_macro_data=0`
- `openbb_ingestion_runs=0`

Status: implemented.

## Overall Verdict
Accepted with low-priority follow-up items. The OpenBB phase is correctly implemented as an optional research/data ingestion layer, not an execution engine.
