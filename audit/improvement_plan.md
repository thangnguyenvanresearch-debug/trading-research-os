# Improvement plan

## Fix immediately

1. Làm Freqtrade CLI backtest path thật.
   - File: `src/freqtrade_brain/batch_backtest_runner.py`
   - Việc cần làm: truyền `--userdir`, `--config`, strategy class name đúng, `--export`, `--export-filename`; gọi `freqtrade_result_parser.py`; lưu metrics thật vào DB.
   - Acceptance: chạy `python scripts/run_freqtrade_backtests.py --use-freqtrade-cli` không trả `_empty_metrics()` nếu CLI thành công.

2. Tách sample data khỏi real Freqtrade data.
   - File: `src/data_brain/freqtrade_data_adapter.py`, `scripts/download_crypto_data.py`
   - Việc cần làm: thêm flag explicit `--sample`; khi `--use-freqtrade-cli`, đọc file OHLCV Freqtrade đã tải thay vì sinh sample.
   - Acceptance: report/log source là `freqtrade_cli_import`, không phải `sample_freqtrade_adapter`.

3. Sửa decision engine để không hardcode symbol và không xóa lịch sử.
   - File: `src/decision_brain/decision_engine.py`
   - Việc cần làm: tạo decisions theo symbol/pair hoặc strategy-pair; giữ append-only history hoặc upsert theo `(strategy_id, symbol, run_id)`.
   - Acceptance: multi-pair specs tạo decision cho từng pair; bảng decisions không bị truncate mỗi lần score.

4. Thêm `.gitignore`.
   - File: `.gitignore`
   - Việc cần làm: ignore `.env`, `data/**`, `database/*.duckdb`, `reports/**`, `__pycache__/`, `.pytest_cache/`, generated runtime outputs nếu không muốn version.
   - Lưu ý: Không xóa file trong audit-only; đây là task sửa sau audit.

## Fix next

1. Mở rộng risk gate.
   - File: `src/risk_brain/risk_gate.py`
   - Thêm dry-run divergence check từ `paper_trading_logs`.
   - Thêm generated-code/spec look-ahead review result.
   - Thêm `archived` workflow và rule rõ cho `approved_for_dry_run`.

2. Tăng chất lượng parser metrics.
   - File: `src/freqtrade_brain/freqtrade_result_parser.py`, `database/schema.sql`
   - Thêm best/worst pair, average profit, fee-adjusted riêng, slippage-adjusted riêng, pair-level stats.

3. Thêm integration tests cho pipeline v1.
   - Dùng temp database/temp dirs.
   - Test: data -> features -> specs -> convert -> fallback backtest -> risk -> decision.
   - Test: missing Freqtrade/LEAN/Qlib không làm dashboard/core crash.

4. Strengthen strategy spec validation.
   - Dùng schema typed rõ hơn.
   - Validate bounds cho stop loss, take profit, max trades, exposure, timeframe.
   - Validate condition object type trước khi `.get()`.

## Improve later

1. OpenBB adapter thật.
   - Pull context/market/macro data khi package có sẵn.
   - Normalize vào DuckDB/Parquet.

2. LEAN integration phase 3.
   - Generate project thật, strategy skeleton usable, run CLI, parse portfolio metrics.

3. Qlib integration phase 3.
   - Dataset builder thật từ local market data.
   - Experiment config, model report, signal export.

4. Dashboard cockpit nâng cấp.
   - Show engine health, missing dependency warnings, dry-run readiness, rejection reason drilldown.
   - Show pair-level leaderboard và current regime per symbol.

5. Data quality hardening.
   - Gap detection, timezone normalization, OHLC sanity, duplicate by symbol/timeframe/source, stale data warnings.

## Optional v2

1. NautilusTrader event-driven adapter thật.
2. Hummingbot order book collector/paper market making config generator hoàn chỉnh.
3. FinceptTerminal-style TUI/terminal analytics shell.
4. Walk-forward and purged cross-validation modules.
5. Model registry versioning for Qlib experiments.

