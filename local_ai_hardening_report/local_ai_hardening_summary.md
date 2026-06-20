# Local AI Hardening Summary

## Files changed

Source/test files:

- `src/ai/local_ai_client.py`
- `src/ai/research_engine.py`
- `src/dashboard/pages/12_local_ai_research.py`
- `tests/test_local_ai_client.py`
- `tests/test_research_engine.py`

Report files:

- `local_ai_hardening_report/local_ai_hardening_summary.md`
- `local_ai_hardening_report/local_ai_hardening_details.md`
- `local_ai_hardening_report/local_ai_hardening_findings.json`

Runtime artifact:

- `reports/local_ai/memo_ce24bd4ef54c_market_review.md`

## Fixes implemented

1. Enforced `allow_external_api: false` independently.
   - Non-localhost endpoints are rejected unless `allow_external_api` is explicitly true.
   - `safe_mode: true` still rejects non-localhost endpoints.
   - `api.openai.com` and `chatgpt.com` hosts are never allowed.
   - Localhost and `127.0.0.1` remain allowed.

2. Narrowed Local AI optional DB fetch behavior.
   - Missing optional tables return empty context and record a warning.
   - Unexpected DB/query errors are not silently swallowed.

3. Reduced dashboard unavailable delay.
   - Local AI status on `src/dashboard/pages/12_local_ai_research.py` is cached with Streamlit `st.cache_data(ttl=45)`.

## Tests run

- `python -m compileall src scripts -q`: passed
- `python -m compileall src/dashboard -q`: passed
- `python -m pytest -q`: passed, `66 passed`
- Local AI CLI unavailable-path smoke test: passed

## Ollama availability

Ollama was **not available** on `http://localhost:11434`.

Observed:

```text
ollama_unavailable: URLError
```

## Real memo generation

No real local memo was generated because Ollama was unavailable.

A failed/unavailable memo was saved safely:

- memo_id: `memo_ce24bd4ef54c`
- status: `failed`
- report path: `reports/local_ai/memo_ce24bd4ef54c_market_review.md`

## Remaining issues

No required remediation issues remain from this pass.

Future manual step after starting Ollama:

```powershell
ollama pull qwen2.5:7b
python scripts/run_local_ai_research.py --symbols AAPL MSFT --provider yfinance --interval 1d --task-type market_review
```

## Safety confirmation

No OpenAI API, `OPENAI_API_KEY`, ChatGPT OAuth, cookies, browser automation, password handling, live trading, futures, leverage, or real orders were added.

Safety grep hits were limited to:

- denylist code rejecting `api.openai.com` / ChatGPT hosts;
- config flags set to false;
- tests asserting forbidden behavior;
- README explanatory text;
- existing OpenBB secret-redaction regex.
