# Daily Research Reliability Details

## Commands run

### Compile

`.\.venv-openbb\Scripts\python.exe -m compileall src scripts -q`

Result: passed.

### Tests

`.\.venv-openbb\Scripts\python.exe -m pytest -q`

Result: passed.

Summary:

```text
86 passed in 30.31s
```

### Daily pipeline rerun 1

`powershell -ExecutionPolicy Bypass -File scripts\run_daily_research_venv.ps1`

Result: command passed, pipeline status `partial_failed`.

Summary:

```text
run_id=daily_512b40bc3058
status=partial_failed
symbols=AAPL,MSFT
provider=yfinance
interval=1d
analytics_report_path=D:\AI2\QuantGit\trading-research-os\reports\daily_research\daily_512b40bc3058\daily_research_summary.md
local_ai_memo_id=memo_2c20e56a6d74
local_ai_report_path=D:\AI2\QuantGit\trading-research-os\reports\local_ai\memo_2c20e56a6d74_daily_research_note.md
warnings=Context markdown truncated to 12000 characters.; URLError: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it>
errors=URLError: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it>
```

OpenBB normalized:

```text
AAPL rows=1115
MSFT rows=1115
```

Daily metadata:

```json
{
  "fresh_status": "completed",
  "rows_inserted": 0,
  "rows_failed": 0,
  "rows_skipped_duplicate": 2230,
  "dedupe_enabled": true,
  "local_ai_preflight_status": "not_available",
  "local_ai_model_available": false,
  "local_ai_retry_attempts_used": 0,
  "local_ai_compact_retry_used": false,
  "local_ai_status": "unavailable"
}
```

### Daily pipeline rerun 2

`powershell -ExecutionPolicy Bypass -File scripts\run_daily_research_venv.ps1`

Result: command passed, pipeline status `partial_failed`.

Summary:

```text
run_id=daily_ba8422817abb
status=partial_failed
symbols=AAPL,MSFT
provider=yfinance
interval=1d
analytics_report_path=D:\AI2\QuantGit\trading-research-os\reports\daily_research\daily_ba8422817abb\daily_research_summary.md
local_ai_memo_id=memo_0decbd93ecaa
local_ai_report_path=D:\AI2\QuantGit\trading-research-os\reports\local_ai\memo_0decbd93ecaa_daily_research_note.md
warnings=Context markdown truncated to 12000 characters.; URLError: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it>
errors=URLError: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it>
```

Daily metadata:

```json
{
  "fresh_status": "completed",
  "rows_inserted": 0,
  "rows_failed": 0,
  "rows_skipped_duplicate": 2230,
  "dedupe_enabled": true,
  "local_ai_preflight_status": "not_available",
  "local_ai_model_available": false,
  "local_ai_retry_attempts_used": 0,
  "local_ai_compact_retry_used": false,
  "local_ai_status": "unavailable"
}
```

### DB verification

Query:

```sql
SELECT symbol, provider, interval, COUNT(*) AS rows, COUNT(DISTINCT timestamp) AS distinct_timestamps
FROM openbb_market_data
GROUP BY symbol, provider, interval
ORDER BY symbol;
```

Result:

```text
symbol  provider interval  rows  distinct_timestamps
AAPL    yfinance 1d        2230  1115
MSFT    yfinance 1d        2230  1115
```

Query:

```sql
SELECT memo_id, status, model, LENGTH(response_text) AS response_len
FROM ai_research_memos
ORDER BY created_at DESC
LIMIT 5;
```

Result:

```text
memo_0decbd93ecaa failed    qwen2.5:3b 0
memo_2c20e56a6d74 failed    qwen2.5:3b 0
memo_a7179ad2aa04 failed    qwen2.5:3b 0
memo_15a2221eb8b2 completed qwen2.5:3b 2183
memo_afcc82129ce5 completed qwen2.5:3b 2021
```

### Duplicate dry-run

`.\.venv-openbb\Scripts\python.exe scripts\dedupe_openbb_market_data.py --limit 5`

Result: passed; no rows deleted.

Summary:

```text
OpenBB market data dedupe dry-run. No rows were deleted.
symbol asset_class provider interval  timestamp  duplicate_count
AAPL   equity      yfinance 1d        2022-01-03 2
AAPL   equity      yfinance 1d        2022-01-04 2
AAPL   equity      yfinance 1d        2022-01-05 2
AAPL   equity      yfinance 1d        2022-01-06 2
AAPL   equity      yfinance 1d        2022-01-07 2
```

### Dashboard HTTP check

`.\.venv-openbb\Scripts\python.exe -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8501', timeout=10).status)"`

Result:

```text
200
```

### Safety grep

Search scope: `configs src scripts tests README.md`.

Result: no unsafe enablement found.

Observed hits were limited to:

- negative README statements
- config fields set to false
- tests asserting forbidden strings are absent
- Local AI forbidden host denylist
- redaction regex / provider credential warning text

## Failed commands

Several initial DB verification one-liners failed due to PowerShell quoting around SQL strings. They did not modify project state. The same queries were rerun successfully through a Python here-string.

## Duplicate handling details

The new ingestion path dedupes future inserts by logical key:

```text
symbol + asset_class + provider + interval + timestamp
```

Existing duplicates were intentionally not deleted automatically. The new dry-run cleanup script makes this visible and requires explicit `--apply`.

## Local AI retry details

Runtime validation did not exercise a successful live retry because Ollama was unavailable at localhost during both reruns. Unit tests verified:

- transient `RemoteDisconnected` retries and succeeds on a later call
- requested model missing fails before generation
- forbidden OpenAI/ChatGPT hosts are rejected without retry
- research engine compact retry succeeds after an initial transient failure

## Remaining issues

- Existing duplicate OpenBB rows remain until an explicit maintenance cleanup is run.
- Start Ollama before scheduler execution if a completed daily Local AI memo is required:
  `ollama list`
  then rerun:
  `powershell -ExecutionPolicy Bypass -File scripts\run_daily_research_venv.ps1`
