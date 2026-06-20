# LEAN Integration Summary

## Files changed

- `configs/lean.yaml`
- `configs/engine_registry.yaml`
- `configs/daily_research.yaml`
- `database/schema.sql`
- `src/lean_brain/lean_adapter.py`
- `src/lean_brain/lean_data_bridge.py`
- `src/lean_brain/lean_project_builder.py`
- `src/lean_brain/lean_runner.py`
- `src/lean_brain/lean_backtest_runner.py`
- `src/lean_brain/lean_result_parser.py`
- `scripts/run_lean_backtest.py`
- `src/dashboard/pages/14_lean_backtests.py`
- `tests/test_lean_adapter.py`
- `tests/test_lean_data_bridge.py`
- `tests/test_lean_runner.py`
- `README.md`

## LEAN status

- LEAN CLI available: `false`
- Docker available: `true`
- Mode: `research_only`
- safe_for_live: `false`
- Current capability: local OpenBB data export and LEAN-style project skeleton generation.

## Local data export

Local OpenBB data was exported to:

- `data/generated/lean/data/AAPL_yfinance_1d.csv`
- `data/generated/lean/data/MSFT_yfinance_1d.csv`
- `data/generated/lean/data/data_manifest.json`

Rows exported:

- AAPL: `1115`
- MSFT: `1115`

The manifest labels the files as `LEAN research bridge data`.

## Skeleton created

Skeleton smoke test:

```powershell
python scripts\run_lean_backtest.py --symbols AAPL MSFT --provider yfinance --interval 1d --strategy-name equal_weight_demo --skip-run
```

Result:

- run_id: `lean_bt_f9a4224eb9c6`
- status: `skeleton_created`
- project_path: `D:\AI2\QuantGit\trading-research-os\data\generated\lean\projects\equal_weight_demo_lean_495bed575415`
- report_path: `D:\AI2\QuantGit\trading-research-os\reports\lean\lean_bt_f9a4224eb9c6_equal_weight_demo.md`

## Local LEAN backtest wrapper

Normal wrapper smoke test:

```powershell
python scripts\run_lean_backtest.py --symbols AAPL MSFT --provider yfinance --interval 1d --strategy-name equal_weight_demo
```

Result:

- run_id: `lean_bt_496f6c073884`
- status: `unavailable`
- project_path: `D:\AI2\QuantGit\trading-research-os\data\generated\lean\projects\equal_weight_demo_lean_d41360a694ff`
- report_path: `D:\AI2\QuantGit\trading-research-os\reports\lean\lean_bt_496f6c073884_equal_weight_demo.md`
- warning: LEAN CLI is not installed.

No metrics were invented because no LEAN result/statistics file existed.

## Tests and checks

- `python -m compileall src scripts -q`: passed
- `python -m compileall src/dashboard -q`: passed
- `python -m pytest -q`: passed, `102 passed`
- Dashboard HTTP check: `http://localhost:8501` returned `200`

## Safety confirmation

No OpenAI API, ChatGPT OAuth, cookies, browser automation, password handling, brokerage credentials, QuantConnect cloud credentials, live trading, futures, leverage, or real orders were added.

Safety grep found only safety documentation, false config flags, tests, denylist/redaction code, and explicit research-only warnings.

## Remaining issues

- LEAN CLI is not installed, so executable LEAN backtests are not verified.
- Docker is available, but unused because LEAN CLI is missing.
- Generated LEAN project is a research-only skeleton until LEAN CLI is installed and a local backtest succeeds.
