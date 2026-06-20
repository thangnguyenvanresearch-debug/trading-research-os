# Follow-up Codex fix prompt

You are Codex working in `D:\AI2\QuantGit\trading-research-os`.

Mode: implement fixes. Do not enable live trading, futures, leverage, or real orders. Keep all execution backtest-only or dry-run/paper-only.

Use the audit files in `audit/` as source of truth. Fix only verified issues below.

## Priority 1: Make Freqtrade data/backtest path honest

1. Update `scripts/download_crypto_data.py` and `src/data_brain/freqtrade_data_adapter.py`.
   - Add an explicit `--sample` flag.
   - Default may remain sample only if documented, but `--use-freqtrade-cli` must not silently ingest generated sample data.
   - When `--use-freqtrade-cli` is used, import actual downloaded Freqtrade OHLCV files from `data/freqtrade` if present.
   - Store source as `freqtrade_cli_import` for imported files and `sample_freqtrade_adapter` only for sample data.
   - If CLI download succeeds but files cannot be imported, fail with a clear message.

2. Update `src/freqtrade_brain/batch_backtest_runner.py`.
   - Replace `_run_freqtrade_cli()` placeholder metrics.
   - Run Freqtrade with explicit userdir/config/export filename.
   - Parse exported result with `src/freqtrade_brain/freqtrade_result_parser.py`.
   - Store standardized metrics in `backtest_metrics`.
   - If Freqtrade CLI is missing, keep the internal fallback path unchanged and clearly label it as research fallback.

3. Update `src/freqtrade_brain/freqtrade_result_parser.py`.
   - Parse total return, max drawdown, win rate, trade count, profit factor, Sharpe/Sortino when available.
   - Add avg win/loss, best/worst pair if available.
   - Return defaults only for absent fields, not as replacement for a successful CLI run.

## Priority 2: Fix decision history and per-symbol output

1. Update `src/decision_brain/decision_engine.py`.
   - Remove `DELETE FROM decisions`.
   - Do not hardcode `"BTC/USDT"`.
   - Emit decisions per pair from strategy specs or pair-level metrics where available.
   - Preserve historical decisions. Use deterministic upsert only if keyed by `strategy_id`, `symbol`, and latest `run_id`.
   - Keep allowed permissions limited to `REJECTED`, `WATCHLIST`, `PAPER_ONLY`, `APPROVED_FOR_DRY_RUN`.

## Priority 3: Strengthen risk gate

1. Update `src/risk_brain/risk_gate.py`.
   - Use `material_dry_run_divergence` from `configs/risk_rules.yaml` when paper/dry-run data exists.
   - Add a hook/input for look-ahead audit result from spec/generated strategy checks.
   - Add a real `archived` path for old/replaced strategies.
   - Add explicit rules for `approved_for_dry_run`; do not approve live.

## Priority 4: Repo hygiene

1. Add `.gitignore`.
   - Ignore `.env`, `data/**`, `database/*.duckdb`, `reports/**`, `__pycache__/`, `.pytest_cache/`.
   - Preserve folder structure with `.gitkeep` only if needed.

2. Move generated runtime outputs out of `src/` where practical.
   - Specs and generated strategies can be under `data/generated/` or another configured runtime directory.
   - Keep traceability back to YAML specs.

## Priority 5: Tests

Add tests for:

- Safe defaults: no `APPROVED_FOR_LIVE`, live/futures/leverage false.
- Missing optional engine behavior for OpenBB/Qlib/LEAN/Nautilus.
- Full v1 fallback pipeline using temp dirs/temp database.
- Freqtrade parser using a small fixture JSON.
- Decision engine preserves history and emits non-hardcoded symbols.
- Risk gate rejects dry-run divergence when data exists.

Do not implement unrelated UI redesigns or full Qlib/LEAN/Hummingbot/Nautilus integrations in this pass.

