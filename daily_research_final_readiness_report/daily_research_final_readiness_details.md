# Daily Research Final Readiness Details

## Commands run

### Compile

```powershell
.\.venv-openbb\Scripts\python.exe -m compileall src scripts -q
```

Result: passed.

### Tests

```powershell
.\.venv-openbb\Scripts\python.exe -m pytest -q
```

Result:

```text
86 passed in 25.74s
```

### Duplicate dry-run

```powershell
.\.venv-openbb\Scripts\python.exe scripts\dedupe_openbb_market_data.py --limit 20
```

Result: passed, no rows deleted.

Sample output:

```text
OpenBB market data dedupe dry-run. No rows were deleted.
symbol asset_class provider interval  timestamp  duplicate_count
AAPL   equity      yfinance 1d        2022-01-03 2
AAPL   equity      yfinance 1d        2022-01-04 2
AAPL   equity      yfinance 1d        2022-01-05 2
...
```

### Row count before cleanup

```sql
SELECT symbol, provider, interval, COUNT(*) AS rows, COUNT(DISTINCT timestamp) AS distinct_timestamps
FROM openbb_market_data
GROUP BY symbol, provider, interval
ORDER BY symbol;
```

Result:

```text
symbol provider interval rows distinct_timestamps
AAPL   yfinance 1d       2230 1115
MSFT   yfinance 1d       2230 1115
```

### Duplicate cleanup apply

```powershell
.\.venv-openbb\Scripts\python.exe scripts\dedupe_openbb_market_data.py --apply
```

Result:

```json
{
  "duplicates_found": 4460,
  "rows_deleted": 2230,
  "rows_kept": 2230,
  "backup_path": "D:\\AI2\\QuantGit\\trading-research-os\\reports\\maintenance\\openbb_market_data_duplicates_2026-06-14T150431_0000.csv"
}
```

### Row count after cleanup

Result:

```text
symbol provider interval rows distinct_timestamps
AAPL   yfinance 1d       1115 1115
MSFT   yfinance 1d       1115 1115
```

### Ollama version

```powershell
.\.venv-openbb\Scripts\python.exe -c "import urllib.request; print(urllib.request.urlopen('http://localhost:11434/api/version', timeout=10).read().decode())"
```

Result:

```json
{"version":"0.30.8"}
```

### Ollama tags

```powershell
.\.venv-openbb\Scripts\python.exe -c "import urllib.request; print(urllib.request.urlopen('http://localhost:11434/api/tags', timeout=10).read().decode()[:1000])"
```

Result: passed. The output included `qwen2.5:3b`.

### Daily pipeline rerun

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_daily_research_venv.ps1
```

Result:

```text
Ollama available: true (0.30.8)
run_id=daily_262063e1ff1f
status=completed_with_warnings
symbols=AAPL,MSFT
provider=yfinance
interval=1d
analytics_report_path=D:\AI2\QuantGit\trading-research-os\reports\daily_research\daily_262063e1ff1f\daily_research_summary.md
local_ai_memo_id=memo_d03ffe674cfe
local_ai_report_path=D:\AI2\QuantGit\trading-research-os\reports\local_ai\memo_d03ffe674cfe_daily_research_note.md
warnings=Context markdown truncated to 12000 characters.
```

Latest run metadata:

```json
{
  "fresh_openbb_ingestion_status": "completed",
  "fresh_openbb_ingestion_rows_inserted": 0,
  "fresh_openbb_ingestion_rows_failed": 0,
  "fresh_openbb_ingestion_rows_skipped_duplicate": 2230,
  "fresh_openbb_ingestion_dedupe_enabled": true,
  "local_ai_preflight_status": "ok",
  "local_ai_model_available": true,
  "local_ai_retry_attempts_used": 0,
  "local_ai_compact_retry_used": false,
  "local_ai_status": "ok",
  "local_ai_error": null
}
```

### DB verification

Latest daily runs:

```text
daily_262063e1ff1f completed_with_warnings memo_d03ffe674cfe errors=[]
```

Latest AI memos:

```text
memo_d03ffe674cfe completed qwen2.5:3b response_len=588
```

Market row counts:

```text
AAPL yfinance 1d rows=1115 distinct_timestamps=1115
MSFT yfinance 1d rows=1115 distinct_timestamps=1115
```

### Dashboard check

```powershell
.\.venv-openbb\Scripts\python.exe -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8501', timeout=10).status)"
```

Result:

```text
200
```

### Scheduler helper print-only check

```powershell
powershell -ExecutionPolicy Bypass -File scripts\create_daily_research_task.ps1
```

Result:

```text
Daily research scheduled task preview
Task name: TradingResearchOSDailyResearch
Working directory: D:\AI2\QuantGit\trading-research-os
Command: powershell.exe -ExecutionPolicy Bypass -File "D:\AI2\QuantGit\trading-research-os\scripts\run_daily_research_venv.ps1"
Schedule time: 08:00

Default behavior is print-only. Use -Register to create the scheduled task.
Printed only; no task was registered.
```

Command to register later:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\create_daily_research_task.ps1 -Register -At "08:30"
```

This was not run.

### Safety grep

Search scope:

```text
configs src scripts tests README.md
```

Patterns included OpenAI API keys, OpenAI/ChatGPT endpoints, OAuth, cookies, browser automation, password/credential handling, order-placement strings, live trading flags, leverage/futures flags, and live approval states.

Result: no unsafe enablement found. Hits were limited to:

- README negative explanations
- config fields set to false
- tests asserting forbidden strings are absent
- Local AI forbidden-host denylist
- OpenBB provider warning text
- redaction regex

## Remaining issues

- No scheduler-readiness blockers remain.
- DuckDB is unavailable, so SQLite fallback is being used. For larger historical datasets, install DuckDB support later.
