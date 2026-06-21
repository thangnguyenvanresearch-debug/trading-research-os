# File-Level Findings MVP Release

## `.gitignore`

Good coverage for env files, generated data/reports, database files, Python caches, coverage and IDE files. Minor gap: `.venv-openbb/`, `.ruff_cache/`, and runtime logs are only local-excluded.

## `README.md`

Accurately positions the project as research-only. LEAN/Qlib limitations and no-live/no-order boundary are explicit.

## `docs/PRODUCT_OVERVIEW.md`

Accurate product framing. It explicitly rejects live trading and buy/sell advice.

## `docs/ARCHITECTURE.md`

Accurate local data, Local AI, daily pipeline, LEAN, Qlib, storage and safety flows.

## `docs/DEMO_SCRIPT.md`

Commands are practical and do not require credentials, LEAN executable backtest, or installed Qlib trainer.

## `docs/CURRENT_STATE.md`

Test count is current at `137 passed`. Optional engine limitations and scheduler-state caveat are accurate. Runtime Ollama availability is dynamic and currently unavailable.

## `docs/RELEASE_CHECKLIST.md`

Contains compile, pytest, dashboard, scheduler, Ollama, duplicates, safety grep, secrets, backups, commit and tag checks.

## `scripts/health_check.py`

Read-only status collection. No engine execution, internet data fetch, credential handling or order path found.

## `src/dashboard/pages/00_research_control_center.py`

Read-only status page. Shows required engine/data/safety state and LEAN caveat. No API key, credential, live toggle or order controls found.

## Git Tracked Files

346 tracked files. No `.venv-openbb`, runtime database, generated reports/data, secrets file, or large binary artifact tracked.
