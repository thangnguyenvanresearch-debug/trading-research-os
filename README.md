# Multi-Brain AI Trading Research OS

Local-first research OS for market data ingestion, feature engineering, strategy specification, controlled strategy conversion, backtesting, risk review, scoring, and decision display.

This project is for research, backtesting, paper trading, and strategy validation first. It does not enable real-money live trading by default, does not implement leverage or futures by default, and does not place real orders. Backtest results are not proof of future profit.

## Quickstart

```bash
cd trading-research-os
python -m pip install -e .
python scripts/init_database.py
python scripts/health_check.py
streamlit run src/dashboard/app.py
```

For the current product/demo package, read:

- [Product overview](docs/PRODUCT_OVERVIEW.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Demo script](docs/DEMO_SCRIPT.md)
- [Current state](docs/CURRENT_STATE.md)
- [Release checklist](docs/RELEASE_CHECKLIST.md)

## Current Capabilities

- OpenBB local yfinance ingestion and analytics for research data.
- Freqtrade-compatible crypto research/backtest path.
- Local AI research memos through Ollama, without OpenAI API or ChatGPT OAuth.
- Daily Research Pipeline via Windows Task Scheduler and `.venv-openbb` runner.
- Read-only Research Control Center dashboard.
- LEAN local data bridge and research skeleton creation.
- Qlib no-lookahead dataset export from local OpenBB rows.
- CLI health check and report generation.

## Known Limitations

- LEAN executable backtest remains unverified after Docker/runtime timeout.
- Qlib true trainer remains future work while Qlib package is missing.
- Control Center shows latest daily DB run; it does not prove current Task Scheduler state.
- Research outputs are not trading advice.

## Research-Only Safety Boundary

The project must remain local research tooling: no OpenAI API, no ChatGPT OAuth, no browser login automation, no brokerage credentials, no cloud credentials, no live trading, no futures, no leverage, and no real orders.

## Architecture

```text
Market data -> Feature brain -> Regime detector -> YAML strategy specs
            -> Controlled engine converters -> Backtests -> Risk gate
            -> Score + decision engine -> Streamlit decision cockpit
```

The v1 working path is crypto research with Freqtrade-compatible strategy generation. External engines are optional and isolated behind adapters.

## Engine Roles

| Tool | Current status | Role |
|---|---|---|
| OpenBB | partial / optional ingestion | Market data and research context connector, not execution. |
| FinceptTerminal | scaffold only / future UI inspiration | Finance-terminal UX inspiration for future analytics modules. |
| Qlib | partial / optional research | Local OpenBB feature dataset export and optional Qlib ML/factor experiment wrapper. |
| LEAN | partial / optional local research | Research-only local OpenBB data bridge, LEAN-style project skeletons, and optional local LEAN CLI backtest wrapper. |
| Freqtrade | partially implemented / v1 focus | Crypto spot strategy conversion, fallback backtesting, CLI-result parsing, and optional dry-run config. |
| Hummingbot | partial paper/scanner lab | Phase 4 paper-only market making and arbitrage lab. |
| NautilusTrader | scaffold only / v2 | Future event-driven architecture target, not required for v1. |

## Setup

```bash
cd trading-research-os
python -m pip install -e .
python scripts/init_database.py
```

If DuckDB is installed, the database layer uses DuckDB. If not, it falls back to SQLite using the same local database path so the skeleton remains runnable. Install DuckDB explicitly with `python -m pip install -e .[database]` if you want DuckDB in a fresh environment.

## Run V1

```bash
python scripts/download_crypto_data.py --sample --pairs BTC/USDT ETH/USDT SOL/USDT --timeframe 1h
python scripts/build_features.py
python scripts/generate_strategy_specs.py --asset-class crypto --count 3
python scripts/convert_specs_to_freqtrade.py
python scripts/run_freqtrade_backtests.py
python scripts/score_strategies.py
streamlit run src/dashboard/streamlit_app.py
```

`--sample` creates deterministic synthetic candles for demo/testing only. It is not market data. Add `--use-freqtrade-cli` after installing and configuring Freqtrade if you want to download and import actual Freqtrade OHLCV files. CLI mode never silently falls back to sample data.

## Optional Engines

Install and configure each engine separately. This repository uses adapters and CLI wrappers rather than copying external repository code.

- Freqtrade: install the CLI, keep `dry_run: true`, and use spot mode.
- LEAN: install LEAN CLI for phase 3 portfolio research.
- Qlib: install Qlib for factor and ML experiments.
- OpenBB: install OpenBB for broader market and macro context.
- Hummingbot: use paper-only configs and alert/scanner workflows first.
- NautilusTrader: planned event-driven simulation/live consistency target for v2.

## OpenBB Ingestion

OpenBB is an optional research/data context adapter. It can ingest market and macro data into local storage for research, feature engineering, dashboard context, and future strategy filters. It does not execute trades, create broker configs, or place orders.

Install optional engine dependencies when you want to use OpenBB:

```bash
python -m pip install -e .[engines]
```

Then run a local ingestion job:

```bash
python scripts/ingest_openbb_data.py --symbols AAPL MSFT NVDA --asset-class equity --start-date 2022-01-01 --interval 1d
```

OpenBB ingestion stores normalized rows in:

- `openbb_market_data`
- `openbb_macro_data`
- `openbb_ingestion_runs`
- `openbb_research_context` for future curated summaries
- `data/openbb/market_data/` as Parquet when available, or CSV fallback

The dashboard page `OpenBB Ingestion` reads existing local ingestion results and shows engine status, latest runs, warnings/errors, and data previews. Ingestion should be run from the CLI so missing packages, provider errors, or credential requirements are explicit.

Some providers may require API keys or paid plans. This project does not store keys or require credentials by default. Prefer no-key/free providers where available, and treat provider failures as research data availability issues, not strategy signals.

Known limitations:

- OpenBB APIs vary by version, so the adapter uses defensive endpoint discovery.
- Provider availability and schemas may change.
- Data quality is not guaranteed.
- No trading decision should rely on one data source only.

## OpenBB Local Analytics

After ingesting OpenBB data, the dashboard reads the local database only. It does not fetch external data on page load and does not require credentials. The OpenBB page shows descriptive analytics such as return summary, max drawdown, annualized volatility for daily data, data quality checks, normalized price comparison, and return correlation.

You can also generate a local CSV summary:

```bash
python scripts/report_openbb_analytics.py --symbols AAPL MSFT --provider yfinance --interval 1d
```

These analytics are descriptive research context, not trading advice. They do not create signals by themselves, do not place orders, and do not enable live trading.

## LEAN Research-Only Integration

LEAN is an optional local research/backtest engine for equity/ETF-style strategies. This project exports local OpenBB OHLCV rows into a simple "LEAN research bridge data" CSV format, creates a LEAN-style project skeleton, and can attempt a local LEAN CLI backtest only if LEAN CLI is installed.

Safety boundaries:

- No QuantConnect cloud login.
- No brokerage credentials.
- No live trading mode.
- No futures.
- No leverage.
- No real orders.
- If LEAN CLI or Docker is missing, the system records an unavailable/skeleton status and continues.

Create a research-only skeleton without running LEAN:

```bash
python scripts/run_lean_backtest.py --symbols AAPL MSFT --provider yfinance --interval 1d --strategy-name equal_weight_demo --skip-run
```

If LEAN CLI is installed locally and configured for local backtests:

```bash
python scripts/run_lean_backtest.py --symbols AAPL MSFT --provider yfinance --interval 1d --strategy-name equal_weight_demo
```

Outputs are stored locally:

- `lean_backtest_runs`
- `lean_backtest_metrics`
- `data/generated/lean/data/`
- `data/generated/lean/projects/`
- `reports/lean/`

Dashboard page:

```text
src/dashboard/pages/14_lean_backtests.py
```

The dashboard shows LEAN CLI/Docker status, latest local research runs, warnings/errors, and parsed metrics when available. It does not expose API key inputs, brokerage settings, live mode, or order controls.

## Qlib Research-Only Integration

Qlib is an optional ML/factor research engine. This project uses local OpenBB rows to build a Qlib-style research feature dataset and records experiment runs locally. Qlib is not an execution engine here: it does not place orders, does not use brokerage credentials, does not fetch remote datasets by default, and does not enable live trading.

Dataset export works even when Qlib is not installed:

```bash
python scripts/run_qlib_experiment.py --symbols AAPL MSFT --provider yfinance --interval 1d --experiment-name qlib_demo --skip-run
```

If Qlib is installed locally, the wrapper can attempt a local research experiment:

```bash
python scripts/run_qlib_experiment.py --symbols AAPL MSFT --provider yfinance --interval 1d --experiment-name qlib_demo
```

Outputs are stored locally:

- `qlib_dataset_exports`
- `qlib_experiment_runs`
- `qlib_predictions` only when real predictions exist
- `data/generated/qlib/datasets/`
- `reports/qlib/`

The feature dataset includes trailing features such as returns, momentum, volatility, and volume z-score. The forward return is stored as a separate label column for research only; it is not used as an input feature.

Dashboard page:

```text
src/dashboard/pages/15_qlib_research.py
```

The dashboard shows Qlib package status, dataset exports, experiment runs, metrics when available, warnings/errors, and predictions only when real predictions exist. It has no API key inputs, no cloud credential controls, no live trading controls, and no order controls.

## Local AI Mode

Local AI Mode adds fully automated research memo generation through an Ollama-compatible local model. It reads local database rows, builds a structured research context, sends that context to `http://localhost:11434` by default, stores the memo in `ai_research_memos`, and writes a markdown copy under `reports/local_ai/`.

This mode does not use the OpenAI API, does not require an OpenAI API key, does not use ChatGPT OAuth, does not store cookies or browser sessions, and does not automate ChatGPT login. ChatGPT Plus is not an official API backend for this local app.

Install Ollama separately, then pull a local model:

```bash
ollama pull llama3.1:8b
# or
ollama pull qwen2.5:7b
```

Run a local AI research memo:

```bash
python scripts/run_local_ai_research.py --symbols AAPL MSFT --provider yfinance --interval 1d --task-type market_review
```

Optional context flags:

```bash
python scripts/run_local_ai_research.py --symbols AAPL MSFT --provider yfinance --interval 1d --task-type daily_research_note --include-backtests --include-risk --include-decisions
```

Dashboard page:

```text
src/dashboard/pages/12_local_ai_research.py
```

The dashboard can run local AI research only when clicked by the user. It reads local data, calls the configured local Ollama endpoint, and displays stored memos. It does not fetch OpenBB/provider data from page load, does not create buy/sell controls, and does not place orders.

If Ollama is not installed or not running, the CLI and dashboard fail gracefully and save/show a local AI unavailable warning.

## Daily Auto Research Pipeline

The Daily Auto Research Pipeline runs a one-command research workflow: optional OpenBB/yfinance data update, local analytics report generation, and Local AI memo generation through Ollama. It is research-only automation. It does not use OpenAI API, does not use ChatGPT OAuth, does not store cookies or browser sessions, does not automate browser login, and does not place real orders.

Run:

```bash
python scripts/run_daily_research.py --symbols AAPL MSFT --provider yfinance --interval 1d --task-type daily_research_note --model qwen2.5:3b
```

On Windows, prefer the venv runner when `.venv-openbb` contains OpenBB:

```powershell
.\scripts\run_daily_research_venv.ps1
.\scripts\run_daily_research_venv.ps1 --symbols AAPL MSFT --provider yfinance --interval 1d --task-type daily_research_note --model qwen2.5:3b
```

Dry run without external data or Local AI calls:

```bash
python scripts/run_daily_research.py --symbols AAPL MSFT --provider yfinance --interval 1d --task-type daily_research_note --model qwen2.5:3b --dry-run
```

Outputs are stored locally:

- `daily_research_runs` table
- `reports/daily_research/<run_id>/openbb_summary.csv`
- `reports/daily_research/<run_id>/daily_research_summary.json`
- `reports/daily_research/<run_id>/daily_research_summary.md`
- `ai_research_memos` and `reports/local_ai/` when Local AI is enabled

Dashboard page:

```text
src/dashboard/pages/13_daily_research.py
```

The dashboard page can trigger the local pipeline only after a user clicks `Run daily research now`. It has no API key inputs, no OAuth controls, no buy/sell controls, and no live trading controls.

Optional Windows helper:

```powershell
.\scripts\create_daily_research_task.ps1
.\scripts\create_daily_research_task.ps1 -Register -At "08:30"
```

By default, the helper only prints the scheduled command and uses `scripts/run_daily_research_venv.ps1`. It registers a Windows task only when `-Register` is explicitly passed. It does not store passwords, API keys, cookies, browser sessions, or exchange credentials.

## Strategy Specs

AI or template generation must produce YAML first. The validator checks schema, indicators, operators, no leverage, no futures, fee/slippage requirements, and suspicious future-looking logic. Engine code is generated only by controlled converters.

Example:

```yaml
strategy_name: trend_pullback_rsi_atr_v1
asset_class: crypto
engine_target: freqtrade
timeframe: 1h
pairs:
  - BTC/USDT
risk:
  leverage_allowed: false
  futures_allowed: false
```

## Adding A Strategy Template

Add a new dictionary to `src/ai_strategy_brain/strategy_generator.py`, using only indicators listed in `strategy_spec_schema.py`. Then run:

```bash
python scripts/generate_strategy_specs.py --asset-class crypto --count 10
python scripts/convert_specs_to_freqtrade.py
```

## Backtests And Scoring

`scripts/run_freqtrade_backtests.py` uses Freqtrade when explicitly requested and available. Otherwise it runs a small internal spot-only research fallback backtester to produce v1 pipeline metrics. The fallback is for demo/research validation only and is not a replacement for full Freqtrade or LEAN engine tests.

Real Freqtrade CLI results require an exported JSON file. The runner requests a Freqtrade export and parses common result fields into the local metrics schema. Missing fields are recorded as parser warnings.

The score is 0 to 100:

- 25% out-of-sample performance
- 20% drawdown control
- 15% return quality
- 15% trade count reliability
- 15% market regime fit
- 10% fee/slippage robustness

## Cleaner Demo Output

`scripts/score_strategies.py` preserves append-only history by default, so repeated local demo runs can print decisions from older backtest runs. Use output filters when you want a quieter console:

```bash
python scripts/score_strategies.py --latest-only
python scripts/score_strategies.py --run-id bt_example123
```

These options only filter console output. They do not delete historical decisions, truncate risk reviews, or modify backtest history.

For a completely clean demo database, use a disposable project copy or temporarily point `database_path` in `configs/global.yaml` to a disposable file such as `database/demo.sqlite`, run the demo workflow, then restore the original config. Do not delete the main research database for a demo.

## Dashboard

The dashboard is a decision cockpit:

- Research Control Center: unified read-only status for engines, latest runs, safety checks, data health, and next actions.
- Market Cockpit: regime, chart, indicators, latest signal, risk status.
- Strategy Factory: generated YAML, rationale, validation and conversion status.
- Backtest Leaderboard: ranking, return, drawdown, win rate, trades, profit factor, status.
- Risk Gate: rejections, flags, overfit warnings.
- Crypto Freqtrade: generated strategies and readiness.
- Equity LEAN + Qlib: local LEAN research hooks and Qlib-style local factor dataset exports.
- Market Making Lab: paper-only spread and inventory experiments.
- Arbitrage Scanner: alert-only opportunities.
- Nautilus Future Engine: v2 migration target.

## Research Control Center

The Research Control Center is a read-only dashboard page for the whole local research OS. It summarizes OpenBB data, Local AI, Daily Research, LEAN, Qlib, engine registry status, latest runs, safety state, data health, reports, and static next-action recommendations.

It does not run external ingestion on page load, does not call an LLM for recommendations, does not ask for credentials, does not use cloud login, does not expose API key forms, and does not place orders.

Status wording is intentionally conservative. LEAN may show CLI/data-skeleton availability, but executable LEAN backtests remain unverified until the Docker/runtime execution completes successfully. Qlib dataset export is available, but the true Qlib trainer remains future work while the Qlib package is missing. The Control Center is read-only and does not execute orders.

Launch:

```bash
streamlit run src/dashboard/app.py
```

Optional CLI status report:

```bash
python scripts/report_control_center_status.py
```

Reports are written under:

```text
reports/control_center/
```

## Safety Defaults

- Live real-money trading is disabled.
- Leverage is disabled.
- Futures are disabled.
- Hummingbot is paper/alert-only.
- Highest v1 permission is `APPROVED_FOR_DRY_RUN`.
- There is no `APPROVED_FOR_LIVE` state in v1.

## Round 3 Hardening

- AST-based static look-ahead checks now supplement forbidden-token scanning for generated Python strategy code.
- SQLite fallback now logs a clear warning when DuckDB is unavailable, with the install command for DuckDB support.
- Optional engine diagnostics are standardized and explicitly report current capability, next step, and `safe_for_live: false`.
- Live trading, futures, leverage, and real orders remain disabled.

## Limitations

The included internal backtester is for pipeline validation, not a replacement for full Freqtrade/LEAN engine tests. Synthetic sample data is for demo only. Qlib dataset export is research infrastructure, not proof of alpha. Qlib, LEAN, Hummingbot, OpenBB, and Nautilus integrations are intentionally adapter-first in v1. Strategy performance can be overfit, regime-dependent, fee-sensitive, or caused by data issues.

## Troubleshooting

- Freqtrade not installed: use `--sample` for demo data, or install Freqtrade before using `--use-freqtrade-cli`.
- No downloaded data found: run Freqtrade `download-data` with JSON, JSON.GZ, or Feather output under `data/freqtrade`, then rerun the import.
- Parser cannot find expected metrics: check the generated export in `reports/freqtrade`; missing fields are shown as parser warnings on the dashboard.
- DuckDB missing: install `.[database]` or rely on SQLite fallback.
- Dashboard shows missing engines: OpenBB, Qlib, LEAN, Hummingbot, and Nautilus are optional in v1 and should not block the crypto fallback pipeline. If Qlib is missing, `scripts/run_qlib_experiment.py --skip-run` can still export a local research dataset.
