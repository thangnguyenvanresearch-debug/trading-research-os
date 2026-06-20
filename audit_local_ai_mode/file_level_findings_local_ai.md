# File-level Findings Local AI

## `configs/local_ai.yaml`

Status: **implemented**

- Ollama provider configured.
- Localhost default endpoint.
- Safe flags disabled for external/OpenAI/ChatGPT/browser automation.
- Controlled task list exists.

Finding: `allow_external_api:false` is not independently enforced in the client if `safe_mode` is manually disabled.

## `database/schema.sql`

Status: **implemented**

- `ai_research_memos` table exists.
- Required fields present.
- SQLite verified through `init_database.py`.

DuckDB runtime: Không xác minh được vì DuckDB không available trong env base.

## `src/ai/local_ai_client.py`

Status: **implemented**

- Uses `urllib`, not OpenAI/ChatGPT SDK.
- Calls local Ollama `/api/version` and `/api/generate`.
- Uses `stream: False`.
- Safe-mode rejects non-localhost.
- Structured result/error returned.

Low issue: `allow_external_api` config field is not checked directly.

## `src/ai/research_engine.py`

Status: **implemented**

- Builds local DB context.
- Includes OpenBB analytics and optional backtest/risk/decision context.
- Builds constrained research prompt.
- Saves memo to DB and markdown report.
- Unavailable Ollama path stores failed memo.

Low issue: `_safe_fetch()` catches all exceptions and can hide non-missing-table DB errors.

## `scripts/run_local_ai_research.py`

Status: **implemented**

- Imports `_bootstrap.py`, so research-only safety assertion runs.
- Supports expected CLI flags.
- Handles unavailable Ollama without crash.
- Prints memo metadata.

## `src/dashboard/pages/12_local_ai_research.py`

Status: **implemented**

- Shows Local AI status.
- Shows latest memos.
- Lets user run local AI research via button.
- Shows prompt/context preview.
- No OpenAI API key form.
- No ChatGPT OAuth/cookies/browser automation.
- No order controls.

Low issue: local health check on page load may introduce delay when Ollama is down.

## `tests/test_local_ai_client.py`

Status: **implemented**

- Covers unavailable status.
- Covers safe-mode non-local rejection.
- Covers mocked Ollama generation.
- Checks no order surface and no OpenAI/ChatGPT backend strings.

## `tests/test_research_engine.py`

Status: **implemented**

- Covers prompt safety language.
- Covers empty DB context.
- Covers mocked OpenBB rows.
- Covers unavailable Local AI memo insert.
- Covers mocked completed memo insert.
- Covers optional backtest/risk/decision context.

## `README.md`

Status: **implemented**

- Documents Local AI Mode.
- Explains no OpenAI API, no ChatGPT OAuth/cookies/session/browser automation.
- Documents Ollama install/pull examples and CLI usage.
- States dashboard behavior and unavailable handling.
