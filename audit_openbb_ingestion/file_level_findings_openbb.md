# File-Level Findings OpenBB

## `configs/openbb.yaml`
Status: implemented.

- Safe editable defaults exist.
- `safe_mode: true` and `allow_credentials: false` are present.
- Provider priority and default universe are configured.

## `configs/engine_registry.yaml`
Status: implemented.

- OpenBB status is `partial`.
- `safe_for_live: false`.
- `execution_allowed: false`.

## `database/schema.sql`
Status: implemented.

- Adds `openbb_market_data`.
- Adds `openbb_macro_data`.
- Adds `openbb_ingestion_runs`.
- Adds `openbb_research_context`.
- SQLite execution verified through `init_database.py`.
- DuckDB execution: Không xác minh được.

## `src/core/database.py`
Status: implemented.

- Existing initializer executes full schema and can create OpenBB tables.
- SQLite fallback warning remains clear.

## `src/data_brain/openbb_adapter.py`
Status: partially implemented.

- Real adapter structure exists.
- Missing package status is safe.
- Ingestion result object exists.
- Market normalization is implemented.
- One-symbol failure is handled.
- Macro ingestion is best-effort.
- File persistence uses `data/openbb` paths.
- No live execution methods found.
- Real OpenBB provider calls are not verifiable because OpenBB is not installed.
- File is large; consider splitting later.

## `scripts/ingest_openbb_data.py`
Status: implemented.

- CLI supports expected arguments.
- Uses `_bootstrap`, which calls `assert_research_only()`.
- Missing OpenBB path exits gracefully.
- No credential requirement or order controls.

## `src/dashboard/pages/10_openbb_ingestion.py`
Status: implemented.

- Reads DB only.
- Shows engine status, ingestion runs, market preview, macro preview.
- Does not launch external fetch on page load.
- No live trading/order controls.

## `src/dashboard/streamlit_app.py`
Status: implemented.

- Existing engine status includes `get_openbb_status()`.
- No unsafe OpenBB controls found.

## `src/feature_brain/openbb_feature_bridge.py`
Status: partially implemented.

- Reads local OpenBB data and converts to common OHLCV feature input shape.
- Does not couple Freqtrade pipeline to OpenBB.
- Missing-table guard is absent.

## `tests/test_openbb_adapter.py`
Status: implemented.

- Covers missing status, normalization, partial symbol failure, no order functions, and CLI missing package.
- No internet/OpenBB dependency.

## `README.md`
Status: implemented.

- Documents OpenBB ingestion, storage, dashboard display, provider limitations, and no execution behavior.
