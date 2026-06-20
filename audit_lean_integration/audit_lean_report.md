# Full Audit Report: LEAN Research-Only Integration

## Scope

Audit tập trung vào LEAN integration mới:

- config
- schema
- adapter/status
- OpenBB local data bridge
- LEAN project skeleton
- runner/parser
- CLI
- dashboard page
- tests
- smoke commands
- safety invariants

Không sửa source code. Các smoke command có tạo runtime artifacts/report/DB run records theo đúng yêu cầu audit, nhưng không sửa source files.

## Commands Run

```powershell
python scripts\init_database.py
python -m compileall src scripts -q
python -m compileall src\dashboard -q
python -m pytest -q
python scripts\run_lean_backtest.py --symbols AAPL MSFT --provider yfinance --interval 1d --strategy-name equal_weight_demo --skip-run
python scripts\run_lean_backtest.py --symbols AAPL MSFT --provider yfinance --interval 1d --strategy-name equal_weight_demo
```

Additional verification:

- queried `lean_backtest_runs`
- queried `lean_backtest_metrics`
- checked exported CSV row counts and duplicate timestamps
- checked `get_lean_status()`
- checked dashboard HTTP `http://localhost:8501`
- ran safety grep over `configs src scripts tests README.md`

## Safety Audit

Status: **implemented / safe**

Evidence:

- [configs/lean.yaml](D:\AI2\QuantGit\trading-research-os\configs\lean.yaml)
  - `mode: research_only`
  - `allow_live_trading: false`
  - `allow_brokerage_credentials: false`
  - `allow_quantconnect_cloud: false`
  - `allow_real_orders: false`
  - `allow_futures: false`
  - `allow_leverage: false`
- [src/lean_brain/lean_adapter.py](D:\AI2\QuantGit\trading-research-os\src\lean_brain\lean_adapter.py)
  - `assert_lean_research_only()` rejects live/broker/cloud/orders/futures/leverage.
  - `get_lean_status()` does not install, login, or request credentials.
- [scripts/run_lean_backtest.py](D:\AI2\QuantGit\trading-research-os\scripts\run_lean_backtest.py)
  - imports `_bootstrap`, which calls project research-only guard.
- [src/dashboard/pages/14_lean_backtests.py](D:\AI2\QuantGit\trading-research-os\src\dashboard\pages\14_lean_backtests.py)
  - no API key form, no broker form, no live toggle, no order controls.

Safety grep found only:

- negative README statements
- false config flags
- tests asserting forbidden strings are absent
- Local AI denylist/redaction references
- LEAN research-only warning labels

No unsafe enablement found.

## Config Audit

Status: **implemented**

Files:

- [configs/lean.yaml](D:\AI2\QuantGit\trading-research-os\configs\lean.yaml)
- [configs/engine_registry.yaml](D:\AI2\QuantGit\trading-research-os\configs\engine_registry.yaml)
- [configs/daily_research.yaml](D:\AI2\QuantGit\trading-research-os\configs\daily_research.yaml)

Findings:

- LEAN is optional.
- Engine registry marks LEAN as `partial`, `safe_for_live: false`, `execution_allowed: local_backtest_only`.
- Daily pipeline config has:
  - `lean.enabled: false`
  - `run_backtest: false`

Conclusion: daily auto pipeline does not run LEAN by default.

## Schema Audit

Status: **implemented**

File:

- [database/schema.sql](D:\AI2\QuantGit\trading-research-os\database\schema.sql)

Tables exist:

- `lean_backtest_runs`
- `lean_backtest_metrics`

Required fields exist:

- `lean_backtest_runs`: `run_id`, `created_at`, `finished_at`, `status`, `symbols`, `strategy_name`, `engine_status`, `command_text`, `project_path`, `report_path`, `metrics_json`, `warnings_json`, `errors_json`, `metadata_json`
- `lean_backtest_metrics`: `metric_id`, `run_id`, `symbol`, `metric_name`, `metric_value`, `metric_text`, `created_at`

`python scripts\init_database.py` passed under SQLite fallback. DuckDB is unavailable in this environment.

## LEAN Adapter Audit

Status: **implemented**

File:

- [src/lean_brain/lean_adapter.py](D:\AI2\QuantGit\trading-research-os\src\lean_brain\lean_adapter.py)

Verified:

- Missing LEAN CLI returns safe status.
- Docker check is optional.
- No install attempt.
- No QuantConnect login.
- No credential request.
- `safe_for_live` is false.
- unsafe config flags raise `ValueError`.

Runtime status:

```json
{
  "lean_cli_available": false,
  "docker_available": true,
  "safe_for_live": false,
  "status": "missing"
}
```

## Data Bridge Audit

Status: **implemented**

File:

- [src/lean_brain/lean_data_bridge.py](D:\AI2\QuantGit\trading-research-os\src\lean_brain\lean_data_bridge.py)

Verified:

- Reads only `openbb_market_data`.
- No external fetch.
- Dedupes by `symbol`, `asset_class`, `provider`, `interval`, `timestamp`.
- Sorts by symbol/timestamp.
- Exports one CSV per symbol.
- Writes `data_manifest.json`.
- Labels output as `LEAN research bridge data`.
- Handles missing table/empty rows safely.

CSV verification:

```text
AAPL_yfinance_1d.csv 1115 rows, 1115 unique timestamps, 0 duplicates
MSFT_yfinance_1d.csv 1115 rows, 1115 unique timestamps, 0 duplicates
```

## Project Builder Audit

Status: **implemented with minor caution**

File:

- [src/lean_brain/lean_project_builder.py](D:\AI2\QuantGit\trading-research-os\src\lean_brain\lean_project_builder.py)

Creates:

- `README.md`
- `strategy_config.json`
- `Main.py`
- `local_data_manifest.json`

Skeleton clearly states:

- research-only
- no live trading
- no brokerage credentials
- no QuantConnect cloud login
- no futures
- no leverage
- no real orders

Minor caution:

- Generated `Main.py` uses LEAN `SetHoldings()` inside a local backtest skeleton. This is acceptable as a backtest portfolio instruction and not a real order path, but it should be re-audited after LEAN CLI is installed.

## Runner Audit

Status: **implemented**

Files:

- [src/lean_brain/lean_runner.py](D:\AI2\QuantGit\trading-research-os\src\lean_brain\lean_runner.py)
- [src/lean_brain/lean_backtest_runner.py](D:\AI2\QuantGit\trading-research-os\src\lean_brain\lean_backtest_runner.py)
- [src/lean_brain/lean_result_parser.py](D:\AI2\QuantGit\trading-research-os\src\lean_brain\lean_result_parser.py)

Verified:

- `--skip-run` creates skeleton only.
- Missing LEAN CLI returns status `unavailable`, no crash.
- Report saved under `reports/lean/`.
- DB run record saved.
- Parser is best-effort and does not invent metrics.
- `lean_backtest_metrics` remains empty when no LEAN result exists.

Normal run result:

```text
run_id=lean_bt_a0e709b0ac00
status=unavailable
warnings=["LEAN CLI is not installed; only data export and research skeleton generation are available."]
errors=[]
```

## CLI Audit

Status: **implemented**

File:

- [scripts/run_lean_backtest.py](D:\AI2\QuantGit\trading-research-os\scripts\run_lean_backtest.py)

Verified:

- Imports `_bootstrap` safety guard.
- Supports `--symbols`, `--provider`, `--interval`, `--strategy-name`, `--cash`, `--skip-run`.
- No credentials.
- No cloud login.
- No live trading option.
- Missing LEAN CLI path exits cleanly.

## Dashboard Audit

Status: **implemented**

File:

- [src/dashboard/pages/14_lean_backtests.py](D:\AI2\QuantGit\trading-research-os\src\dashboard\pages\14_lean_backtests.py)

Verified:

- Shows LEAN CLI/Docker status.
- Shows latest runs.
- Shows project/report paths.
- Shows warnings/errors.
- Shows metrics only if available.
- No API key input.
- No brokerage credential form.
- No QuantConnect cloud login.
- No live trading toggle.
- No order controls.
- Local run button only appears if LEAN CLI is available.

HTTP check:

```text
http://localhost:8501 -> 200
```

Visual browser inspection was not automated.

## Tests Audit

Status: **passed**

```text
102 passed in 18.20s
```

Tests cover:

- unavailable LEAN status
- research-only config enforcement
- OpenBB data export/dedupe
- project skeleton creation
- CLI parse for `--skip-run`
- unavailable runner path
- parser no-metrics behavior
- dashboard compile
- no order/cloud unsafe surface

## Regression / Runtime Notes

- Smoke commands created additional runtime records and generated LEAN artifacts. This is expected from the requested audit commands.
- No source files were modified.
- DuckDB remains unavailable; SQLite fallback works.

## Remaining Risk

- Executable LEAN backtest not verified because LEAN CLI is unavailable.
- Generated skeleton should be re-audited after installing LEAN CLI and running a real local backtest.

