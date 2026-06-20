# File-Level Findings - Qlib Integration

## `configs/qlib.yaml`

Status: **implemented / safe**

- `mode: research_only`
- `safe_for_live: false`
- unsafe flags are false
- uses local OpenBB as data source
- output under `data/generated/qlib`
- reports under `reports/qlib`

## `configs/engine_registry.yaml`

Status: **implemented**

- Qlib moved to `partial`.
- `execution_allowed: research_only`.
- `safe_for_live: false`.
- `requires_optional_package: true`.

## `configs/daily_research.yaml`

Status: **implemented**

- Qlib daily block present but disabled.
- `qlib.enabled: false`.
- `qlib.run_experiment: false`.

## `database/schema.sql`

Status: **implemented**

- Adds `qlib_dataset_exports`.
- Adds `qlib_experiment_runs`.
- Adds `qlib_predictions`.
- SQLite fallback initialized successfully.

## `src/qlib_brain/qlib_adapter.py`

Status: **implemented / safe**

- Missing Qlib handled through import check.
- No installation.
- No cloud calls.
- Research-only guard rejects unsafe flags.
- `safe_for_live: false`.

## `src/qlib_brain/qlib_data_bridge.py`

Status: **implemented**

- Reads local `openbb_market_data`.
- Dedupes and sorts data.
- Builds trailing features.
- Separates future return as label.
- Writes CSV and manifest.
- Saves `qlib_dataset_exports`.

No-lookahead status: **verified by source inspection**.

## `src/qlib_brain/qlib_runner.py`

Status: **partially implemented**

- Good unavailable path.
- Records run/report.
- Does not fake metrics/predictions when Qlib missing.

Low issue:

- If Qlib is installed, current path runs a pandas baseline placeholder and may write baseline predictions to `qlib_predictions`. It is labeled research-only, but not a true Qlib trainer.

## `src/qlib_brain/qlib_experiment_runner.py`

Status: **implemented**

- Lightweight compatibility wrapper.
- `run_basic_experiment()` no longer mutates DB.

## `scripts/run_qlib_experiment.py`

Status: **implemented**

- Supports required CLI args.
- Imports `_bootstrap`, so project research-only guard runs.
- Smoke tests pass.

## `scripts/run_qlib_experiments.py`

Status: **implemented**

- Backward-compatible status wrapper.

## `src/dashboard/pages/15_qlib_research.py`

Status: **implemented**

- Shows Qlib status, exports, runs, metrics, warnings/errors, and predictions table.
- No API key input, cloud login, live trading toggle, or order controls found.
- Visual not verified because Streamlit was not running.

## `tests/test_qlib_adapter.py`

Status: **implemented**

- Missing Qlib status.
- Unsafe config rejection.

## `tests/test_qlib_data_bridge.py`

Status: **implemented**

- Local data dedupe.
- Feature builder label separation.
- Dataset export and DB row.

Coverage gap: rolling feature formulas could be tested more explicitly.

## `tests/test_qlib_runner.py`

Status: **implemented**

- Skip-run.
- Unavailable path.
- CLI parser.
- Dashboard compile.
- No live/order surface in runtime modules.

## `README.md`

Status: **implemented**

- Documents Qlib as optional research-only integration.
- Explains local OpenBB data, no remote dataset by default, no live trading, no real orders.
