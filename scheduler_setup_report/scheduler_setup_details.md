# Scheduler Setup Details

## Commands run

### Preview helper

```powershell
powershell -ExecutionPolicy Bypass -File scripts\create_daily_research_task.ps1
```

Summary:

```text
Daily research scheduled task preview
Task name: TradingResearchOSDailyResearch
Working directory: D:\AI2\QuantGit\trading-research-os
Command: powershell.exe -ExecutionPolicy Bypass -File "D:\AI2\QuantGit\trading-research-os\scripts\run_daily_research_venv.ps1"
Schedule time: 08:00
Default behavior is print-only. Use -Register to create the scheduled task.
Printed only; no task was registered.
```

### Existing task check

```powershell
Get-ScheduledTask -TaskName "TradingResearchOSDailyResearch" -ErrorAction SilentlyContinue
```

Result:

```text
TASK_NOT_FOUND
```

### Registration

```powershell
powershell -ExecutionPolicy Bypass -File scripts\create_daily_research_task.ps1 -Register -At "08:30"
```

Summary:

```text
TaskName: TradingResearchOSDailyResearch
State: Ready
Registered scheduled task: TradingResearchOSDailyResearch
```

No password, credential, API key, or exchange configuration was requested.

## Verification output

### Task list

```powershell
Get-ScheduledTask -TaskName "TradingResearchOSDailyResearch" | Format-List *
```

Summary:

```text
State: Ready
TaskName: TradingResearchOSDailyResearch
TaskPath: \
Description: Trading Research OS daily local research run
Triggers: MSFT_TaskDailyTrigger
Actions: MSFT_TaskExecAction
```

### Task info before manual run

```powershell
Get-ScheduledTaskInfo -TaskName "TradingResearchOSDailyResearch"
```

Summary:

```text
NextRunTime: 15/06/2026 8:30:00 AM
LastTaskResult: 267011
```

### Action and trigger

Action:

```text
Execute: powershell.exe
Arguments: -ExecutionPolicy Bypass -File "D:\AI2\QuantGit\trading-research-os\scripts\run_daily_research_venv.ps1"
WorkingDirectory: D:\AI2\QuantGit\trading-research-os
```

Trigger:

```text
Enabled: True
StartBoundary: 2026-06-14T08:30:00+07:00
DaysInterval: 1
```

## Manual run

Command:

```powershell
Start-ScheduledTask -TaskName "TradingResearchOSDailyResearch"
```

After 60 seconds:

```text
LastRunTime: 14/06/2026 10:18:28 PM
LastTaskResult: 267009
```

`267009` means the task was still running.

After an additional 60 seconds:

```text
State: Ready
LastTaskResult: 0
NextRunTime: 15/06/2026 8:30:00 AM
```

`0` means the scheduled task process completed successfully.

## DB verification after manual run

Latest daily run:

```text
run_id: daily_ccd5abf71f95
status: completed_with_warnings
memo_id: memo_527fb16be9b4
```

Latest memo:

```text
memo_id: memo_527fb16be9b4
status: completed
model: qwen2.5:3b
response_len: 1947
```

Latest run metadata:

```json
{
  "fresh_openbb_ingestion_status": "completed",
  "fresh_openbb_ingestion_rows_inserted": 0,
  "fresh_openbb_ingestion_rows_skipped_duplicate": 2230,
  "local_ai_preflight_status": "ok",
  "local_ai_model_available": true,
  "local_ai_status": "ok",
  "local_ai_retry_attempts_used": 0,
  "local_ai_compact_retry_used": false
}
```

OpenBB row counts:

```text
AAPL yfinance 1d rows=1115 distinct_timestamps=1115
MSFT yfinance 1d rows=1115 distinct_timestamps=1115
```

## Safety grep

Search scope:

```text
configs src scripts tests README.md
```

Result: no unsafe enablement found.

Observed matches were limited to:

- README negative explanations
- config fields set to false
- tests asserting forbidden strings are absent
- Local AI forbidden-host denylist
- OpenBB provider credential warning text
- redaction regex

## How to disable or delete the task

Disable only:

```powershell
Disable-ScheduledTask -TaskName "TradingResearchOSDailyResearch"
```

Delete:

```powershell
Unregister-ScheduledTask -TaskName "TradingResearchOSDailyResearch" -Confirm:$false
```

## Remaining issues

- No scheduler setup issue remains.
- The run warning about context truncation is expected and non-fatal.
