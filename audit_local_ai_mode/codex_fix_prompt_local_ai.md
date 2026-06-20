# Optional follow-up prompt for Codex

Use this only for low-priority hardening. There are no critical/high/medium Local AI issues.

```text
You are Codex working in:

D:\AI2\QuantGit\trading-research-os

TASK MODE:
Low-risk Local AI hardening only.

Do not rewrite architecture.
Do not add OpenAI API.
Do not add ChatGPT OAuth.
Do not store cookies/browser sessions.
Do not add credentials.
Do not enable live trading, futures, leverage, or real orders.

SOURCE OF TRUTH:
Read:
D:\AI2\QuantGit\trading-research-os\audit_local_ai_mode\remaining_local_ai_issues.md
D:\AI2\QuantGit\trading-research-os\audit_local_ai_mode\file_level_findings_local_ai.md

FIXES:

1. Enforce allow_external_api=false in src/ai/local_ai_client.py.
   If base_url is non-localhost and allow_external_api is not true, reject even when safe_mode=false.
   Keep current safe_mode behavior.
   Add tests.

2. Narrow _safe_fetch() in src/ai/research_engine.py.
   Only swallow known missing-table errors.
   Log warning for missing optional tables.
   Re-raise or surface unexpected DB/query errors.
   Add tests.

3. Optional dashboard usability:
   Cache get_local_ai_status() on src/dashboard/pages/12_local_ai_research.py with a short TTL or add a manual refresh button so Ollama unavailable does not slow page load repeatedly.

Run:
python -m compileall src scripts -q
python -m pytest -q
python scripts/run_local_ai_research.py --symbols AAPL MSFT --provider yfinance --interval 1d --task-type market_review

Confirm no OpenAI API, ChatGPT OAuth, cookies, browser automation, password handling, live trading, futures, leverage, or real orders were added.
```
