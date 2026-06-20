# File-Level Findings - Control Center

## `src/dashboard/control_center.py`

Status: **partially implemented**

Implemented:

- Loads engine registry.
- Reads OpenBB data health.
- Reads latest daily runs, AI memos, LEAN runs, Qlib runs, Qlib exports.
- Builds safety checklist from config.
- Builds static next actions without LLM.
- Handles missing tables using empty DataFrames.
- Writes markdown control center report.

Issues:

- LEAN status card uses `get_lean_status()` raw `status=ready`, which overstates executable readiness.
- Daily Scheduler status is latest DB run, not actual Windows Task Scheduler status.
- `write_control_center_report()` writes a report by design; CLI also calls `initialize_database()`.
- Warning/error fields are not truncated.
- `build_latest_runs()` queries Qlib exports twice.

## `src/dashboard/pages/00_research_control_center.py`

Status: **implemented / safe**

- Read-only page.
- No run buttons.
- No API key fields.
- No credential forms.
- No cloud login.
- No live trading toggles.
- No order controls.
- Shows registry/latest runs/safety/data health/next actions.

Issue:

- LEAN card says `ready`; needs clearer wording.

## `src/dashboard/app.py`

Status: **safe**

- Thin wrapper around existing dashboard app.
- Does not execute engines on import.
- Does not start scheduler or backtests.

## `scripts/report_control_center_status.py`

Status: **implemented with caveat**

- Generates markdown report.
- Does not execute engines.
- No internet required except bounded local AI status through helper.
- Calls `initialize_database()`, which can create schema tables if absent. This is not research data mutation, but not strict DB read-only.

## `tests/test_control_center.py`

Status: **implemented**

Tests cover:

- missing tables
- engine registry load
- safety checklist
- next actions
- structured statuses
- dashboard compile
- CLI report markdown write
- no live/order runtime surface

Coverage gaps:

- No test that LEAN status wording avoids overstatement.
- No test for warning/error truncation.

## `README.md`

Status: **mostly implemented**

- Documents Control Center as read-only.
- Documents no credentials/cloud/orders.
- Documents CLI command.

Gap:

- Control Center section should explicitly mention LEAN executable remains unverified and Qlib true trainer remains future work when applicable.
