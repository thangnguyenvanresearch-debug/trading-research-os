# Product Overview

## What This Product Is

Trading Research OS is a local-first research workspace for market data ingestion, feature engineering, backtest preparation, risk review, Local AI research memos, and dashboard reporting.

It is not a trading bot. It is not a live execution platform. It does not place real orders.

## Problem It Solves

Retail and independent researchers often end up with scattered scripts, unmanaged datasets, unclear backtest history, and unsafe paths from research to execution. This project organizes those pieces into a controlled local workflow:

- ingest data locally;
- build descriptive analytics and features;
- run research-only backtest or dataset export paths;
- record decisions, risks, and reports;
- summarize results in a read-only Control Center.

## Who It Is For

- Researchers validating market data, strategy ideas, and risk gates.
- Builders who want a local demo of multi-engine research workflows.
- Auditors who need traceable outputs, reports, and safety boundaries.
- Operators who want daily research memos without cloud AI APIs.

## Architecture Overview

The core pattern is:

```text
Local data -> database -> analytics/features -> research engines -> reports/dashboard
```

All engines are optional and isolated. The dashboard reads local state and reports; it should not be treated as an execution console.

## Research-Only Safety Boundary

The system is designed around explicit non-execution boundaries:

- no live trading;
- no futures;
- no leverage;
- no brokerage credentials;
- no cloud credentials;
- no OpenAI API;
- no ChatGPT OAuth;
- no browser login automation;
- no real orders.

Outputs are research memos, dataset exports, backtest skeletons, risk reviews, and dashboard status summaries. They are not buy/sell advice.

## Engine List

### OpenBB

OpenBB is used as a research/data ingestion layer. Current local yfinance ingestion works for AAPL and MSFT, with normalized rows stored in local database tables and files.

### Freqtrade Research Path

The v1 crypto path can generate strategy specs, convert to Freqtrade-compatible strategy files, run safe fallback/sample backtests, score strategies, and route them through risk review. This remains a research path.

### Local AI / Ollama

Local AI Mode uses an Ollama-compatible local endpoint. The verified model is `qwen2.5:3b`. It builds local context from database and report records, then saves research memos locally.

### Daily Research Pipeline

The daily pipeline refreshes local data when available, creates analytics reports, runs Local AI memos, and stores run history. It is registered in Windows Task Scheduler through a venv runner.

### LEAN

LEAN integration is research-only. The local data bridge and skeleton creation work. LEAN CLI is installed, but executable LEAN backtest remains unverified after Docker/runtime timeout. This should be treated as partial.

### Qlib

Qlib integration exports local no-lookahead research datasets from OpenBB rows. Qlib package is missing, so true Qlib trainer execution remains future work.

### Control Center

The Control Center is a read-only Streamlit dashboard page that shows engine statuses, latest runs, data health, safety checklist, and static next actions.

## What Works Now

- OpenBB local yfinance data exists for AAPL and MSFT.
- OpenBB data is deduped by symbol/provider/interval/timestamp.
- Local AI memos work with Ollama `qwen2.5:3b`.
- Daily Research Pipeline is registered in Windows Task Scheduler.
- Control Center read-only dashboard exists.
- LEAN data bridge and skeleton creation work.
- Qlib dataset export works.
- Tests pass after the Control Center accuracy cleanup.

## What Is Partial

- LEAN executable backtest is not verified.
- Qlib true trainer is not verified because Qlib is not installed.
- Control Center reports latest daily DB run; it does not prove current Task Scheduler state.
- DuckDB is optional; current environment may fall back to SQLite.

## Explicitly Not Supported

- Real-money trading.
- Broker login or brokerage configs.
- QuantConnect cloud login.
- OpenAI API or ChatGPT OAuth.
- Browser login automation.
- Direct buy/sell recommendations.
- Futures, leverage, or live order placement.

## Future Roadmap

- Verify local executable LEAN backtests after Docker/runtime diagnostics.
- Install and verify Qlib package execution against exported local datasets.
- Add richer data quality reports and dataset lineage.
- Add more provider coverage while preserving no-credential defaults.
- Add release automation around health checks and audit reports.
