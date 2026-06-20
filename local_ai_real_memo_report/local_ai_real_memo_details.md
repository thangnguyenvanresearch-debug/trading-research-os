# Local AI Real Memo Smoke Details

## Commands run

### Baseline

```powershell
python -m compileall src scripts -q
python -m compileall src/dashboard -q
python -m pytest -q
```

Results:

- compile `src scripts`: passed
- compile `src/dashboard`: passed
- pytest: `66 passed in 3.00s`

### Ollama installation check

```powershell
ollama --version
```

Result:

```text
The term 'ollama' is not recognized as a name of a cmdlet, function, script file, or executable program.
```

Classification: Ollama CLI is not installed or not on PATH.

### Ollama service check

```powershell
@'
import urllib.request
try:
    print(urllib.request.urlopen('http://localhost:11434/api/version', timeout=5).read().decode())
except Exception as e:
    print('ollama_unavailable:', type(e).__name__, str(e))
'@ | python -
```

Result:

```text
ollama_unavailable: URLError <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it>
```

Classification: Ollama service is not available on `localhost:11434`.

### Model pull

Skipped.

Reason: `ollama` command is not available. Per instruction, Ollama was not installed silently.

### Real local memo

Skipped.

Reason: no Ollama CLI/service/model available.

Expected manual command after installing/running Ollama:

```powershell
ollama pull qwen2.5:3b
python scripts/run_local_ai_research.py --symbols AAPL MSFT --provider yfinance --interval 1d --task-type market_review --model qwen2.5:3b
```

### Dashboard check

Existing Streamlit process detected:

```text
PID 624, .venv-openbb python, streamlit run src/dashboard/streamlit_app.py
```

HTTP check rerun with here-string after an inline quoting attempt failed:

```powershell
@'
import urllib.request
try:
    print(urllib.request.urlopen('http://localhost:8501', timeout=5).status)
except Exception as e:
    print('dashboard_unavailable:', type(e).__name__, str(e))
'@ | python -
```

Result:

```text
200
```

Visual browser inspection was not automated. Manual verification is still needed for page `12_local_ai_research`.

### Safety grep

Searched:

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

No unsafe integration was found.

Allowed/explained hits:

- `configs/local_ai.yaml`: `allow_chatgpt_oauth: false`
- `src/ai/local_ai_client.py`: `api.openai.com` appears in denylist; `oauth` appears in false default key.
- `src/data_brain/openbb_adapter.py`: existing secret-redaction regex.
- tests: forbidden strings used in assertions.
- README: explanatory text saying these integrations are not used.

## Failed commands

1. `ollama --version`
   - Cause: Ollama is not installed or not on PATH.
   - Source impact: none.

2. Initial inline dashboard HTTP check
   - Cause: PowerShell quoting/SyntaxError from embedded `\n`.
   - Re-run with here-string succeeded.
   - Source impact: none.

## Remaining issues

- Install and start Ollama manually.
- Pull a small local model such as `qwen2.5:3b`.
- Re-run the Local AI CLI command to generate a real completed memo.
