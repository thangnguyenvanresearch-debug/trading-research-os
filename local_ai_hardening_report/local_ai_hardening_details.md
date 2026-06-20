# Local AI Hardening Details

## Source of truth read

- `audit_local_ai_mode/audit_local_ai_summary.md`
- `audit_local_ai_mode/remaining_local_ai_issues.md`
- `audit_local_ai_mode/file_level_findings_local_ai.md`
- `audit_local_ai_mode/codex_fix_prompt_local_ai.md`

## Code changes

### `src/ai/local_ai_client.py`

Added endpoint policy enforcement:

- local endpoints pass;
- forbidden OpenAI/ChatGPT hosts are rejected unconditionally;
- non-localhost endpoints are rejected when `safe_mode=true`;
- non-localhost endpoints are also rejected when `allow_external_api` is not true, even if `safe_mode=false`.

### `src/ai/research_engine.py`

Changed `_safe_fetch()` behavior:

- known missing optional table errors return empty DataFrame and append a warning;
- unexpected errors are re-raised instead of silently returning empty context.

### `src/dashboard/pages/12_local_ai_research.py`

Added Streamlit cache for local AI status:

```python
@st.cache_data(ttl=45, show_spinner=False)
```

This reduces repeated delay when Ollama is unavailable.

### Tests

Added coverage for:

- non-localhost + `safe_mode=false` + `allow_external_api=false` rejection;
- localhost allowed with and without safe mode;
- explicitly enabled non-forbidden external endpoint path with mocked HTTP;
- OpenAI/ChatGPT hosts never allowed;
- missing optional table warning;
- unexpected DB error not silently swallowed.

## Commands run

```powershell
python -m compileall src scripts -q
```

Result: passed.

```powershell
python -m compileall src/dashboard -q
```

Result: passed.

```powershell
python -m pytest -q
```

Result:

```text
66 passed in 2.62s
```

## Ollama check

Command:

```powershell
@'
import urllib.request
try:
    print(urllib.request.urlopen('http://localhost:11434/api/version', timeout=5).read().decode())
except Exception as e:
    print('ollama_unavailable:', type(e).__name__)
'@ | python -
```

Result:

```text
ollama_unavailable: URLError
```

## Local AI CLI smoke test

Command:

```powershell
python scripts/run_local_ai_research.py --symbols AAPL MSFT --provider yfinance --interval 1d --task-type market_review
```

Result:

```text
memo_id=memo_ce24bd4ef54c
status=failed
provider=ollama
model=llama3.1:8b
output_path=D:\AI2\QuantGit\trading-research-os\reports\local_ai\memo_ce24bd4ef54c_market_review.md
error=URLError: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it>
```

The command did not crash and saved a failed/unavailable memo safely.

## DB verification

Latest memos:

```text
memo_ce24bd4ef54c  failed  ollama  llama3.1:8b  market_review
memo_de999fc87977  failed  ollama  llama3.1:8b  market_review
memo_7f75433d3de4  failed  ollama  llama3.1:8b  market_review
```

## Safety grep summary

Search covered:

```text
OPENAI_API_KEY
api.openai.com
chatgpt.com/auth
oauth
cookie
browser automation
playwright
selenium
password
create_order
place_order
market_order
limit_order
live_trading_enabled: true
real_orders_enabled: true
leverage_enabled: true
futures_enabled: true
APPROVED_FOR_LIVE
approved_for_live
```

No unsafe integration or enablement was found.

Allowed/explained hits:

- `src/ai/local_ai_client.py`: `api.openai.com` appears only in the denylist; `oauth` appears in a false default config key.
- `configs/local_ai.yaml`: `allow_chatgpt_oauth: false`.
- tests: forbidden strings used in assertions.
- README: explanatory text saying these integrations are not used.
- `src/data_brain/openbb_adapter.py`: existing secret-redaction regex.

## Manual next step for real local memo

Start/install Ollama outside this project, then run:

```powershell
ollama pull qwen2.5:7b
python scripts/run_local_ai_research.py --symbols AAPL MSFT --provider yfinance --interval 1d --task-type market_review
```
