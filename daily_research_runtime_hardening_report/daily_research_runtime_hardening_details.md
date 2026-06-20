# Daily Research Runtime Hardening Details

## Commands run

### Base environment checks

```powershell
python -m compileall src scripts -q
python -m pytest -q
```

Results:

- compile: passed
- pytest: `79 passed in 17.48s`

### `.venv-openbb` checks

```powershell
.\.venv-openbb\Scripts\python.exe -m compileall src scripts -q
.\.venv-openbb\Scripts\python.exe -m pytest -q
```

Results:

- compile: passed
- pytest: `79 passed in 16.78s`

### Venv runner

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_daily_research_venv.ps1
```

Output summary:

```text
Ollama available: true (0.30.8)
Python: D:\AI2\QuantGit\trading-research-os\.venv-openbb\Scripts\python.exe
run_id=daily_8f479fa817e1
status=partial_failed
symbols=AAPL,MSFT
provider=yfinance
interval=1d
analytics_report_path=D:\AI2\QuantGit\trading-research-os\reports\daily_research\daily_8f479fa817e1\daily_research_summary.md
local_ai_memo_id=memo_a7179ad2aa04
local_ai_report_path=D:\AI2\QuantGit\trading-research-os\reports\local_ai\memo_a7179ad2aa04_daily_research_note.md
warnings=Context markdown truncated to 24000 characters.; RemoteDisconnected: Remote end closed connection without response
errors=RemoteDisconnected: Remote end closed connection without response
```

OpenBB logs confirmed:

```text
OpenBB normalized market data: symbol=AAPL asset_class=equity provider=yfinance interval=1d rows=1115
OpenBB normalized market data: symbol=MSFT asset_class=equity provider=yfinance interval=1d rows=1115
```

## DB verification

Latest run:

```text
run_id=daily_8f479fa817e1
status=partial_failed
provider=yfinance
interval=1d
local_ai_memo_id=memo_a7179ad2aa04
```

Metadata confirms:

```json
{
  "python_executable": "D:\\AI2\\QuantGit\\trading-research-os\\.venv-openbb\\Scripts\\python.exe",
  "python_version": "3.12.10",
  "openbb_installed": true,
  "ollama_available": true,
  "model_requested": "qwen2.5:3b",
  "fresh_openbb_ingestion_attempted": true,
  "fresh_openbb_ingestion_status": "completed",
  "fresh_openbb_ingestion_rows_inserted": 2230,
  "fresh_openbb_ingestion_rows_failed": 0,
  "existing_openbb_rows_used": 4460
}
```

OpenBB rows:

```text
AAPL yfinance 1d rows=2230
MSFT yfinance 1d rows=2230
```

Latest memos:

```text
memo_a7179ad2aa04 failed    ollama qwen2.5:3b daily_research_note response_len=0
memo_15a2221eb8b2 completed ollama qwen2.5:3b daily_research_note response_len=2183
```

## Scheduler helper

Command:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\create_daily_research_task.ps1
```

Result:

- printed task name, working directory, command, schedule time;
- command uses `scripts\run_daily_research_venv.ps1`;
- no task registered because `-Register` was not passed.

Manual registration example:

```powershell
.\scripts\create_daily_research_task.ps1 -Register -At "08:30"
```

## Dashboard check

```powershell
python -m compileall src/dashboard -q
```

Result: passed.

HTTP:

```text
http://localhost:8501 -> 200
```

Manual visual inspection is still recommended for:

- page `13_daily_research`
- page `12_local_ai_research`

## Safety grep

Search terms included:

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
credential
create_order
place_order
market_order
limit_order
buy_order
sell_order
live_trading_enabled: true
real_orders_enabled: true
leverage_enabled: true
futures_enabled: true
APPROVED_FOR_LIVE
approved_for_live
```

No unsafe integration or live/order enablement found.

Allowed/explained hits:

- config flags set to false;
- Local AI denylist for forbidden OpenAI/ChatGPT hosts;
- tests asserting forbidden functions/states are absent;
- README/helper explanatory text saying credentials/passwords/cookies are not stored;
- existing OpenBB redaction regex.

## Remaining issues

1. Local AI failed during the venv daily run because the Ollama service disconnected and then stopped responding. OpenBB ingestion and analytics succeeded.
2. OpenBB table row count doubled to 2230 per symbol because ingestion appends new rows with generated IDs. This is acceptable for smoke testing but future cleanup could deduplicate by symbol/provider/interval/timestamp.
3. Visual dashboard inspection was not automated.
