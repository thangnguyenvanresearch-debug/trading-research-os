# Daily Research Reliability Summary

## Files changed

- `configs/local_ai.yaml`
- `configs/daily_research.yaml`
- `src/data_brain/openbb_adapter.py`
- `src/ai/local_ai_client.py`
- `src/ai/research_engine.py`
- `src/pipeline/daily_research_pipeline.py`
- `src/dashboard/pages/13_daily_research.py`
- `scripts/dedupe_openbb_market_data.py`
- `tests/test_openbb_adapter.py`
- `tests/test_local_ai_client.py`
- `tests/test_research_engine.py`
- `tests/test_daily_research_pipeline.py`

## Dedupe/upsert implementation

- OpenBB market ingestion now performs application-level dedupe before insert using:
  `symbol`, `asset_class`, `provider`, `interval`, `timestamp`.
- Repeated ingestion no longer inserts duplicate logical rows.
- Ingestion result metadata now includes:
  `rows_inserted`, `rows_failed`, `rows_skipped_duplicate`, `rows_updated`, `dedupe_enabled`.
- Existing historical duplicates were not deleted automatically.
- Optional cleanup script added:
  `scripts/dedupe_openbb_market_data.py`
  - default mode is dry-run
  - `--apply` is required before duplicate rows are deleted
  - apply mode backs up affected rows under `reports/maintenance/`

## Local AI retry implementation

- Local AI generation now performs preflight checks:
  - `/api/version`
  - `/api/tags`
  - requested model availability
- Transient local Ollama errors are retried:
  - `RemoteDisconnected`
  - `ConnectionResetError`
  - `TimeoutError`
  - `URLError`
- Research engine can retry with a compact prompt after a transient generation failure.
- Forbidden or external AI endpoints are still rejected and are not retried.
- Defaults tuned for the installed local model:
  - model: `qwen2.5:3b`
  - timeout: `180`
  - max context chars: `12000`
  - retry attempts: `2`
  - retry backoff seconds: `3`

## Test result

- `.venv-openbb\Scripts\python.exe -m compileall src scripts -q`: passed
- `.venv-openbb\Scripts\python.exe -m pytest -q`: passed, `86 passed`

## First rerun result

- Command: `powershell -ExecutionPolicy Bypass -File scripts\run_daily_research_venv.ps1`
- run_id: `daily_512b40bc3058`
- status: `partial_failed`
- memo_id: `memo_2c20e56a6d74`
- OpenBB ingestion status: `completed`
- rows_inserted: `0`
- rows_failed: `0`
- rows_skipped_duplicate: `2230`
- dedupe_enabled: `true`
- Local AI status: `unavailable`
- Local AI error: Ollama localhost endpoint refused connection.

## Second rerun result

- Command: `powershell -ExecutionPolicy Bypass -File scripts\run_daily_research_venv.ps1`
- run_id: `daily_ba8422817abb`
- status: `partial_failed`
- memo_id: `memo_0decbd93ecaa`
- OpenBB ingestion status: `completed`
- rows_inserted: `0`
- rows_failed: `0`
- rows_skipped_duplicate: `2230`
- dedupe_enabled: `true`
- Local AI status: `unavailable`
- Local AI error: Ollama localhost endpoint refused connection.

## Row count verification

- AAPL/yfinance/1d: `2230` rows, `1115` distinct timestamps.
- MSFT/yfinance/1d: `2230` rows, `1115` distinct timestamps.
- Interpretation: existing duplicates remain from earlier runs, but the two new reruns did not add more duplicate rows.

## Memo result

- Latest memo: `memo_0decbd93ecaa`
- status: `failed`
- model: `qwen2.5:3b`
- response length: `0`
- Reason: Ollama service was unavailable/refused connection during validation.

## Dashboard check

- `http://localhost:8501` returned HTTP `200`.
- Page source now exposes latest daily run metadata including duplicate skips and Local AI retry/compact-retry fields.
- Visual browser inspection was not automated in this pass.

## Safety confirmation

- No OpenAI API integration was added.
- No ChatGPT OAuth, cookies, browser sessions, browser-login automation, or password handling was added.
- No live trading, futures, leverage, real-order, or buy/sell execution features were added.
- Safety grep found only negative documentation/assertions, config false flags, denylist checks, and redaction regex references.

## Remaining issues

- Existing OpenBB duplicate rows from previous runs still exist. Use `scripts/dedupe_openbb_market_data.py` in dry-run mode first, then run `--apply` only after manual approval.
- Ollama was not running/listening at `http://localhost:11434` during the two validation reruns, so the retry success path was verified by tests, not by a live memo rerun.
