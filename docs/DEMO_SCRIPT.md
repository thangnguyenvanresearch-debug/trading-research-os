# Demo Script

This is a 10-15 minute demo for the current research-only Trading Research OS.

## 1. Start Dashboard

```bash
streamlit run src/dashboard/app.py
```

Open the Streamlit URL shown in the terminal. If another dashboard process is already running, use that existing URL.

## 2. Show Research Control Center

Open the `Research Control Center` page.

Point out:

- engine status cards;
- engine registry;
- latest runs and artifacts;
- safety checklist;
- OpenBB data health;
- static next actions.

Say clearly: this page is read-only. It does not run engines, ask for credentials, or place orders.

## 3. Show OpenBB Data Health

Show AAPL/MSFT rows in the data health panel.

Useful read-only check:

```bash
python scripts/health_check.py
```

Expected current state: AAPL and MSFT have local yfinance rows with no duplicate timestamps.

## 4. Show Local AI Memo

Open the Local AI dashboard page or inspect the latest memo from the Control Center.

Explain:

- Local AI uses Ollama locally.
- Verified model: `qwen2.5:3b`.
- No OpenAI API key.
- No ChatGPT OAuth.
- Memos are saved locally under `reports/local_ai/`.

## 5. Show Daily Scheduler

Task name:

```text
TradingResearchOSDailyResearch
```

Read-only scheduler check:

```powershell
Get-ScheduledTask -TaskName "TradingResearchOSDailyResearch"
Get-ScheduledTaskInfo -TaskName "TradingResearchOSDailyResearch"
```

Disable or delete later if needed:

```powershell
Disable-ScheduledTask -TaskName "TradingResearchOSDailyResearch"
Unregister-ScheduledTask -TaskName "TradingResearchOSDailyResearch" -Confirm:$false
```

Show latest daily run in the Control Center. Note that the Control Center reports latest DB run and does not independently prove current scheduler state.

## 6. Show LEAN

Explain:

- LEAN CLI is installed.
- Local data bridge and skeleton creation work.
- Executable LEAN backtest remains unverified after Docker/runtime timeout.
- No `lean login`, no QuantConnect cloud credentials, no brokerage config.

Optional skeleton command:

```bash
python scripts/run_lean_backtest.py --symbols AAPL MSFT --provider yfinance --interval 1d --strategy-name equal_weight_demo --skip-run
```

## 7. Show Qlib

Explain:

- Qlib dataset export works from local OpenBB rows.
- Features are no-lookahead; forward return is a separated label.
- Qlib package is missing, so true Qlib trainer execution is future work.

Optional dataset export:

```bash
python scripts/run_qlib_experiment.py --symbols AAPL MSFT --provider yfinance --interval 1d --experiment-name qlib_demo --skip-run
```

## 8. Close With Safety

Close with:

- no live trading;
- no broker credentials;
- no real orders;
- no futures;
- no leverage;
- no OpenAI API;
- no ChatGPT OAuth.

The product is a research OS, not a trading bot.
