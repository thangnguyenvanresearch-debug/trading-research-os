# Audit Qlib Integration - Full Report

## Scope

Audit tập trung vào Qlib research-only integration:

- `configs/qlib.yaml`
- `configs/engine_registry.yaml`
- `configs/daily_research.yaml`
- `database/schema.sql`
- `src/qlib_brain/qlib_adapter.py`
- `src/qlib_brain/qlib_data_bridge.py`
- `src/qlib_brain/qlib_runner.py`
- `src/qlib_brain/qlib_experiment_runner.py`
- `scripts/run_qlib_experiment.py`
- `scripts/run_qlib_experiments.py`
- `src/dashboard/pages/15_qlib_research.py`
- `tests/test_qlib_adapter.py`
- `tests/test_qlib_data_bridge.py`
- `tests/test_qlib_runner.py`
- latest exported dataset under `data/generated/qlib/datasets/qlib_export_b9c5625b0de2`

Không cài Qlib, không chạy remote dataset/cloud, không tạo execution path.

## Commands Run

- `python scripts/init_database.py` - passed
- `python -m compileall src scripts -q` - passed
- `python -m compileall src\dashboard -q` - passed
- `python -m pytest -q` - passed, `120 passed`
- `python scripts\run_qlib_experiment.py --symbols AAPL MSFT --provider yfinance --interval 1d --experiment-name qlib_demo --skip-run` - passed
- `python scripts\run_qlib_experiment.py --symbols AAPL MSFT --provider yfinance --interval 1d --experiment-name qlib_demo` - passed with `status=unavailable`
- DB verification queries for `qlib_dataset_exports`, `qlib_experiment_runs`, `qlib_predictions` - passed
- Dataset validation for latest `features.csv` and `manifest.json` - passed
- Safety grep over `configs src scripts tests README.md` - no unsafe enablement found
- Dashboard HTTP check - failed because Streamlit was not running

## Safety Audit

Status: **implemented / safe**

Không phát hiện:

- OpenAI API integration
- ChatGPT OAuth
- cookies/session/browser automation
- password handling
- cloud credential integration
- brokerage/live/order enablement
- futures/leverage
- remote Qlib dataset fetch

Safety grep có các hit expected:

- README/tests nói về các forbidden terms dưới dạng cảnh báo hoặc negative assertion.
- Configs đặt unsafe flags là `false`.
- `src/ai/local_ai_client.py` có blocklist OpenAI/ChatGPT endpoint.
- `SetHoldings` chỉ nằm trong LEAN local backtest skeleton, không liên quan Qlib.

## Config Audit

Files:

- `configs/qlib.yaml`
- `configs/engine_registry.yaml`
- `configs/daily_research.yaml`

Status: **implemented**

Findings:

- Qlib optional, status `partial`.
- `mode: research_only`.
- `safe_for_live: false`.
- Unsafe flags all false:
  - `allow_live_trading`
  - `allow_real_orders`
  - `allow_brokerage_credentials`
  - `allow_cloud_credentials`
  - `allow_futures`
  - `allow_leverage`
- Daily pipeline Qlib block exists but disabled:
  - `qlib.enabled: false`
  - `qlib.run_experiment: false`

## Schema Audit

File: `database/schema.sql`

Status: **implemented**

Tables present:

- `qlib_dataset_exports`
- `qlib_experiment_runs`
- `qlib_predictions`

Required fields are present:

- `qlib_dataset_exports`: `export_id`, `created_at`, `status`, `symbols`, `provider`, `interval`, `feature_count`, `row_count`, `output_path`, `manifest_path`, `warnings_json`, `errors_json`, `metadata_json`
- `qlib_experiment_runs`: `run_id`, `created_at`, `finished_at`, `status`, `symbols`, `experiment_name`, `qlib_available`, `dataset_export_id`, `report_path`, `metrics_json`, `warnings_json`, `errors_json`, `metadata_json`
- `qlib_predictions`: `prediction_id`, `run_id`, `symbol`, `timestamp`, `score`, `label`, `model_name`, `created_at`, `metadata_json`

`python scripts/init_database.py` passed under current SQLite fallback backend.

## Qlib Adapter Audit

File: `src/qlib_brain/qlib_adapter.py`

Status: **implemented**

Findings:

- Uses `importlib.util.find_spec("qlib")`.
- Does not install Qlib.
- Does not fetch remote datasets.
- Does not call cloud services.
- Missing Qlib returns safe status with warning.
- `safe_for_live` is always false.
- `assert_qlib_research_only()` rejects:
  - live trading
  - real orders
  - brokerage credentials
  - cloud credentials
  - futures
  - leverage

## Qlib Data Bridge Audit

File: `src/qlib_brain/qlib_data_bridge.py`

Status: **implemented**

Findings:

- Reads only `openbb_market_data`.
- No external fetch.
- Dedupes by `symbol`, `asset_class`, `provider`, `interval`, `timestamp`.
- Sorts by `symbol`, `timestamp`.
- Handles missing `openbb_market_data` table by returning empty frame.
- Writes `features.csv` and `manifest.json`.
- Saves DB row to `qlib_dataset_exports`.

No-lookahead review:

- `close_return_1d = close.pct_change(1)` uses past/current data only.
- `close_return_5d = close.pct_change(5)` uses past/current data only.
- `momentum_20d = close.pct_change(20)` uses past/current data only.
- `volatility_20d` uses rolling std of trailing 1-day return.
- `volume_zscore_20d` uses rolling mean/std with current/trailing volume.
- `label_forward_return_5d = close.shift(-horizon) / close - 1` uses future data, but is separated as label.
- Manifest excludes label from `feature_columns` and sets `label_column: label_forward_return_5d`.

Latest dataset validation:

- Path: `data/generated/qlib/datasets/qlib_export_b9c5625b0de2/features.csv`
- Shape: `(2220, 13)`
- Symbols: `AAPL`, `MSFT`
- Duplicate `symbol+timestamp`: `0`
- `label_forward_return_5d`: present
- missing label count: `0` because rows without label are dropped
- manifest rows: `2220`

## Qlib Runner Audit

Files:

- `src/qlib_brain/qlib_runner.py`
- `src/qlib_brain/qlib_experiment_runner.py`

Status: **partially implemented**

Implemented:

- Calls research-only guard.
- Always builds/exports local dataset.
- If Qlib missing:
  - status `unavailable`
  - report created
  - DB run saved
  - no crash
  - no metrics
  - no predictions
- `run_basic_experiment()` is lightweight and no longer mutates DB.

Low issue:

- If Qlib is installed in the future, current branch runs a pandas baseline and may store baseline predictions in `qlib_predictions` with model name `*_pandas_baseline_research_only`. It is labeled, but it is not a true Qlib trainer/predictor. This should be separated or upgraded in the future Qlib execution phase.

## CLI Audit

Files:

- `scripts/run_qlib_experiment.py`
- `scripts/run_qlib_experiments.py`

Status: **implemented**

Supports:

- `--symbols`
- `--provider`
- `--interval`
- `--experiment-name`
- `--horizon-days`
- `--skip-run`

`scripts/run_qlib_experiment.py` imports `_bootstrap`, so project research-only guard is applied. It requires no credentials, no cloud, no live trading, and no order capability.

## Dashboard Audit

File: `src/dashboard/pages/15_qlib_research.py`

Status: **implemented**

Shows:

- Qlib status
- latest dataset exports
- latest experiment runs
- dataset/report paths
- feature/row counts
- metrics JSON
- warnings/errors
- predictions table only from `qlib_predictions`

No API key input, credential input, cloud login, live trading toggle, or order controls found.

HTTP check:

- `localhost:8501` refused connection because Streamlit was not running.
- Visual inspection: **not verified**.

## Test Audit

Status: **passed**

`120 passed`.

Tests cover:

- missing Qlib status
- research-only config rejection
- local OpenBB load/dedupe
- feature builder and separated forward label
- dataset export and DB row
- skip-run
- unavailable run
- no fake predictions when Qlib unavailable
- CLI parser
- dashboard compile
- no live/order credential surface

Coverage gap:

- Tests do not yet verify all rolling feature values manually. Source inspection covers this sufficiently for current simple formulas.

## Smoke Tests

Skip-run:

- run_id: `qlib_run_3ac2315d99a8`
- status: `dataset_exported`
- export_id: `qlib_export_182f756b2b6a`
- metrics_count: `0`
- predictions_count: `0`

Normal run:

- run_id: `qlib_run_045090f920b8`
- status: `unavailable`
- export_id: `qlib_export_b9c5625b0de2`
- report: `D:\AI2\QuantGit\trading-research-os\reports\qlib\qlib_run_045090f920b8_qlib_demo.md`
- metrics_count: `0`
- predictions_count: `0`

## DB Verification

Verified:

- dataset exports exist
- experiment runs exist
- latest unavailable run exists
- `qlib_predictions` is empty
- `metrics_json` is `{}`

No fake metrics/predictions detected.

## Verdict

**accepted_with_minor_followups**

Safe to checkpoint. Qlib execution remains unverified because package is not installed, but local dataset export and unavailable handling are implemented correctly.
