# File-Level Findings: LEAN Integration

## configs/lean.yaml

Status: **implemented**

- Research-only mode explicit.
- All unsafe flags false.
- No credentials or cloud config.

## configs/engine_registry.yaml

Status: **implemented**

- LEAN moved to `partial`.
- `safe_for_live: false`.
- `execution_allowed: local_backtest_only`.

## configs/daily_research.yaml

Status: **implemented**

- `lean.enabled: false`.
- Daily pipeline does not run LEAN by default.

## database/schema.sql

Status: **implemented**

- `lean_backtest_runs` exists with required fields.
- `lean_backtest_metrics` exists with required fields.
- `init_database.py` passed.

## src/lean_brain/lean_adapter.py

Status: **implemented**

- Safe status object.
- Missing LEAN CLI handled.
- Docker check optional.
- `assert_lean_research_only()` blocks unsafe flags.

## src/lean_brain/lean_data_bridge.py

Status: **implemented**

- Reads local DB only.
- Dedupes export.
- Writes CSV + manifest.
- Labels data as research bridge, not production QuantConnect format.

## src/lean_brain/lean_project_builder.py

Status: **partially implemented / acceptable skeleton**

- Creates local project skeleton.
- Research-only safety text present.
- Config JSON disables live/broker/cloud/futures/leverage/orders.
- Uses `SetHoldings()` in generated `Main.py`; acceptable only as local backtest skeleton, not real execution.

## src/lean_brain/lean_runner.py

Status: **implemented**

- `skip_run` works.
- Missing CLI returns `unavailable`, no crash.
- Writes report and DB records.
- Parser does not invent metrics.
- If LEAN CLI exists, command is local `lean backtest <project_path>`.

## scripts/run_lean_backtest.py

Status: **implemented**

- Uses `_bootstrap` safety guard.
- Supports required CLI args.
- No credential/live/cloud options.

## src/dashboard/pages/14_lean_backtests.py

Status: **implemented**

- Shows status/runs/paths/metrics/warnings/errors.
- Run button only shown if LEAN CLI available.
- No credential/live/order controls.

## tests/test_lean_adapter.py

Status: **implemented**

- Tests missing status and unsafe config rejection.

## tests/test_lean_data_bridge.py

Status: **implemented**

- Tests local export and dedupe.

## tests/test_lean_runner.py

Status: **implemented**

- Tests skeleton creation, unavailable runner path, parser no-metrics, dashboard compile, unsafe string surface.

## README.md

Status: **implemented**

- Documents LEAN as optional research-only.
- Explains no cloud/broker/live/orders.
- Provides skip-run and normal commands.

