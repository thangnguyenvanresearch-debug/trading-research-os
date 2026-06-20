# Daily Research Runtime Hardening Summary

## Files changed

- `src/pipeline/daily_research_pipeline.py`
- `scripts/run_daily_research_venv.ps1`
- `scripts/create_daily_research_task.ps1`
- `tests/test_daily_research_pipeline.py`
- `README.md`

Report files:

- `daily_research_runtime_hardening_report/daily_research_runtime_hardening_summary.md`
- `daily_research_runtime_hardening_report/daily_research_runtime_hardening_details.md`
- `daily_research_runtime_hardening_report/daily_research_runtime_hardening_findings.json`

## Runtime hardening implemented

- Added Windows runner: `scripts/run_daily_research_venv.ps1`.
- Runner uses `.venv-openbb\Scripts\python.exe`.
- Runner checks Ollama local service and warns if unavailable.
- Runner supports passthrough arguments.
- Task Scheduler helper now uses `scripts/run_daily_research_venv.ps1`.
- Task Scheduler helper remains print-only by default and registers only with `-Register`.
- Daily run metadata now includes:
  - `python_executable`
  - `python_version`
  - `openbb_installed`
  - `ollama_available`
  - `model_requested`
  - fresh OpenBB ingestion attempted/status/rows
  - existing OpenBB rows used

## Real venv run result

- Command: `powershell -ExecutionPolicy Bypass -File scripts\run_daily_research_venv.ps1`
- Runtime Python: `.venv-openbb\Scripts\python.exe`
- run_id: `daily_8f479fa817e1`
- status: `partial_failed`
- memo_id: `memo_a7179ad2aa04`
- analytics report: `reports/daily_research/daily_8f479fa817e1/daily_research_summary.md`
- local AI report: `reports/local_ai/memo_a7179ad2aa04_daily_research_note.md`

## Fresh OpenBB ingestion

- OpenBB installed in runtime: `true`
- Fresh ingestion attempted: `true`
- Fresh ingestion status: `completed`
- Rows inserted: `2230`
- Rows failed: `0`
- AAPL yfinance 1d rows after run: `2230`
- MSFT yfinance 1d rows after run: `2230`

## Local AI

- Ollama was available at runner start: `true`, version `0.30.8`
- Local AI memo status: `failed`
- Error: `RemoteDisconnected: Remote end closed connection without response`
- After the failure, Ollama service check returned connection refused.

## Tests

- Base `python -m compileall src scripts -q`: passed
- Base `python -m pytest -q`: passed, `79 passed`
- `.venv-openbb\Scripts\python.exe -m compileall src scripts -q`: passed
- `.venv-openbb\Scripts\python.exe -m pytest -q`: passed, `79 passed`

## Dashboard

- Dashboard HTTP check: `http://localhost:8501` returned `200`
- Visual dashboard inspection was not automated.

## Safety confirmation

No OpenAI API, `OPENAI_API_KEY`, ChatGPT OAuth, cookies, browser automation, password handling, live trading, futures, leverage, or real orders were added.
