# Scheduler Setup Summary

## Task

- Task name: `TradingResearchOSDailyResearch`
- Registered: yes
- Schedule: daily at `08:30` local time
- State: `Ready`
- Next run: `2026-06-15 08:30:00`

## Command

```powershell
powershell.exe -ExecutionPolicy Bypass -File "D:\AI2\QuantGit\trading-research-os\scripts\run_daily_research_venv.ps1"
```

Working directory:

```text
D:\AI2\QuantGit\trading-research-os
```

The action uses the venv runner, which uses:

```text
.venv-openbb\Scripts\python.exe
```

## Registration result

- Preview mode was run first and did not register a task.
- Existing task check returned `TASK_NOT_FOUND`.
- A single task was registered with `-Register -At "08:30"`.
- No password or credential prompt occurred.
- The task uses the current user context.

## Manual run

- Manual run performed: yes
- `Start-ScheduledTask -TaskName "TradingResearchOSDailyResearch"` was run once.
- Initial check after 60 seconds showed task still running: `LastTaskResult = 267009`.
- Final check showed:
  - State: `Ready`
  - LastTaskResult: `0`

Latest daily run from manual task launch:

- run_id: `daily_ccd5abf71f95`
- status: `completed_with_warnings`
- memo_id: `memo_527fb16be9b4`
- memo status: `completed`
- memo response length: `1947`
- warning: context markdown truncated to `12000` characters

OpenBB rows remain deduped:

- AAPL/yfinance/1d: `1115` rows, `1115` distinct timestamps
- MSFT/yfinance/1d: `1115` rows, `1115` distinct timestamps

## Disable or delete later

Disable:

```powershell
Disable-ScheduledTask -TaskName "TradingResearchOSDailyResearch"
```

Delete:

```powershell
Unregister-ScheduledTask -TaskName "TradingResearchOSDailyResearch" -Confirm:$false
```

## Safety confirmation

No OpenAI API, ChatGPT OAuth, cookies, browser automation, password handling, live trading, futures, leverage, real orders, or buy/sell execution features were added.

Safety grep found only negative documentation/assertions, config false flags, local denylist checks, provider warning text, and redaction regex references.

## Remaining issues

- None for scheduler setup.
- The latest run status is `completed_with_warnings` only because the research context was truncated to fit the configured local model context budget.
