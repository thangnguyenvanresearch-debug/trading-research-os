# Daily Research Pipeline Summary

## Files changed

- `configs/daily_research.yaml`
- `database/schema.sql`
- `src/core/paths.py`
- `src/pipeline/__init__.py`
- `src/pipeline/daily_research_pipeline.py`
- `scripts/run_daily_research.py`
- `src/dashboard/pages/13_daily_research.py`
- `scripts/create_daily_research_task.ps1`
- `tests/test_daily_research_pipeline.py`
- `README.md`

Report files:

- `daily_research_pipeline_report/daily_research_pipeline_summary.md`
- `daily_research_pipeline_report/daily_research_pipeline_details.md`
- `daily_research_pipeline_report/daily_research_pipeline_findings.json`

## Pipeline capabilities

- One-command daily research workflow.
- Optional OpenBB/yfinance ingestion.
- Local OpenBB analytics summary generation.
- CSV, JSON, and markdown analytics reports under `reports/daily_research/<run_id>/`.
- Local AI memo generation through Ollama/local model.
- Run metadata saved to `daily_research_runs`.
- Dashboard page `13_daily_research.py` shows latest runs, reports, warnings/errors, and memo text.
- Optional Windows Task Scheduler helper prints instructions by default and registers only with `-Register`.

## Dry run result

- Status: `dry_run`
- run_id: `daily_ff7f9d4fa5b9`
- Analytics report: `reports/daily_research/daily_ff7f9d4fa5b9/daily_research_summary.md`
- No OpenBB ingestion or Local AI call executed.

## Real run result

- Status: `completed_with_warnings`
- run_id: `daily_f3e6beb62b78`
- memo_id: `memo_15a2221eb8b2`
- memo response length: `2183`
- Analytics report: `reports/daily_research/daily_f3e6beb62b78/daily_research_summary.md`
- Local AI report: `reports/local_ai/memo_15a2221eb8b2_daily_research_note.md`

Warnings:

- Base Python environment did not have OpenBB installed, so fresh OpenBB ingestion was skipped safely with `missing_openbb`.
- Existing local OpenBB data was still used for analytics and Local AI context.
- Local AI context was truncated to `24000` characters.

## Tests and checks

- `python -m compileall src scripts -q`: passed
- `python -m compileall src/dashboard -q`: passed
- `python -m pytest -q`: passed, `74 passed`
- Dashboard HTTP check: `http://localhost:8501` returned `200`
- Safety grep: no unsafe integration or live/order enablement found.

## Safety confirmation

No OpenAI API, `OPENAI_API_KEY`, ChatGPT OAuth, cookies, browser automation, password handling, live trading, futures, leverage, or real orders were added.
