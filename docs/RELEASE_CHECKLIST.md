# Release Checklist

Use this checklist before tagging or demoing the current research-only Trading Research OS.

## Code Checks

- [ ] Run `python -m compileall src scripts -q`.
- [ ] Run `python -m compileall src/dashboard -q`.
- [ ] Run `python -m pytest -q`.
- [ ] Run `python scripts/health_check.py`.
- [ ] Run `python scripts/health_check.py --write-report --json`.

## Dashboard Checks

- [ ] Launch `streamlit run src/dashboard/app.py`.
- [ ] Open Research Control Center.
- [ ] Confirm engine statuses are conservative.
- [ ] Confirm LEAN is not shown as executable-verified.
- [ ] Confirm Qlib true trainer is not shown as verified when package is missing.
- [ ] Confirm there are no credential forms, live toggles, or order controls.

## Scheduler Checks

- [ ] Run `Get-ScheduledTask -TaskName "TradingResearchOSDailyResearch"`.
- [ ] Run `Get-ScheduledTaskInfo -TaskName "TradingResearchOSDailyResearch"`.
- [ ] Confirm scheduler command uses `scripts/run_daily_research_venv.ps1`.
- [ ] Do not change scheduler behavior during release unless explicitly planned.

## Local Service Checks

- [ ] Check Ollama: `ollama --version`.
- [ ] Check model list: `ollama list`.
- [ ] Confirm `qwen2.5:3b` is present if Local AI demo is planned.

## Data Checks

- [ ] Verify OpenBB rows by symbol/provider/interval.
- [ ] Verify duplicate count is zero for AAPL/MSFT current demo data.
- [ ] Confirm latest Local AI memo exists.
- [ ] Confirm latest daily run exists.

## Safety Checks

- [ ] Run safety grep for forbidden enablement terms.
- [ ] Confirm no secrets or `.env` values are printed in reports.
- [ ] Confirm no live trading/order code was added.
- [ ] Confirm no brokerage or cloud credentials were added.
- [ ] Confirm no OpenAI API or ChatGPT OAuth was added.

## Backup And Release

- [ ] Back up the database file.
- [ ] Back up `reports/`.
- [ ] Back up generated data under `data/generated/` if needed.
- [ ] Review changed files.
- [ ] Commit with a research-only release message.
- [ ] Tag only after tests, dashboard check, and safety checklist pass.
