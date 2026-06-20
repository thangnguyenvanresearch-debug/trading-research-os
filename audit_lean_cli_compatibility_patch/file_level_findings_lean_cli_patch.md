# File-Level Findings - LEAN CLI Compatibility Patch

## `src/lean_brain/lean_adapter.py`

Status: **implemented**

- Detects global `lean` first.
- Falls back to `.venv-openbb\Scripts\lean.exe`.
- Returns `lean_cli_path`.
- Does not install LEAN.
- Does not call `lean login`.
- `safe_for_live` is false.
- `assert_lean_research_only()` rejects unsafe flags.

Low issue:

- `docker_available` only checks Docker executable presence, not daemon availability.

## `src/lean_brain/lean_runner.py`

Status: **implemented**

- Uses explicit `lean_cli_path`.
- Passes `--lean-config <project>\lean.json`.
- Saves DB run record/report even on failure.
- Timeout exception is captured.
- Does not invent metrics.
- No cloud login/brokerage/live mode.

## `src/lean_brain/lean_project_builder.py`

Status: **implemented**

- Generates `strategy_config.json`, `config.json`, `lean.json`, `local_data_manifest.json`, `README.md`, `Main.py`.
- `lean.json` has `live-mode: false`.
- No credential/token/password fields found.
- No brokerage config found.
- README and algorithm file clearly state research-only.

Note:

- `Main.py` uses `SetHoldings`, but only inside a generated local LEAN backtest skeleton. This is acceptable because there is no live/brokerage config and the project explicitly labels it simulation/research-only.

## `tests/test_lean_adapter.py`

Status: **implemented**

- Covers missing LEAN status.
- Covers `.venv-openbb\Scripts\lean.exe` discovery.
- Covers unsafe config rejection.

## `tests/test_lean_runner.py`

Status: **implemented**

- Covers skeleton generation.
- Covers unavailable runner path.
- Covers skip-run.
- Covers runner command includes `--lean-config`.
- Covers parser does not invent metrics.
- Compiles dashboard page.

## `data/generated/lean/projects/equal_weight_demo_lean_5a615f2a482e/lean.json`

Status: **safe local config**

- No secrets found.
- Uses placeholder organization IDs.
- `live-mode` false.
- No brokerage credentials.

## `data/generated/lean/projects/equal_weight_demo_lean_5a615f2a482e/config.json`

Status: **safe**

- Local algorithm metadata only.
- No credentials.

## `reports/lean/lean_bt_f4d0947fa6ef_equal_weight_demo.md`

Status: **accurate failure report**

- Shows timeout after 900 seconds.
- Metrics `{}`.
- No fake success.

## `reports/lean/lean_bt_3f8ecb692783_equal_weight_demo.md`

Status: **accurate skip-run report**

- Shows `skeleton_created`.
- Records data export and skip warning.
- No metrics invented.
