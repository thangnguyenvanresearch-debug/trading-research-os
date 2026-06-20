# Missing, partial, or scaffold-only features

## Repository/tool leverage

| Tool | Trạng thái | Evidence |
|---|---|---|
| OpenBB | scaffold only | `src/data_brain/openbb_adapter.py` chỉ check import và trả placeholder context. |
| FinceptTerminal | mentioned only | Có trong `configs/engine_registry.yaml`; không có `fincept` module trong `src/`. |
| Qlib | scaffold only | `src/qlib_brain/qlib_experiment_runner.py` trả `qlib_not_installed` hoặc placeholder. |
| LEAN | scaffold only | `src/lean_brain/lean_strategy_converter.py` sinh skeleton có `pass`; runner chỉ check CLI. |
| Freqtrade | partially implemented | Có YAML converter, generated strategies, fallback backtester; CLI path chưa parse result thật. |
| Hummingbot | partially implemented/scaffold only | Có spread/inventory/arbitrage functions và paper config; không có Hummingbot connector hoặc order book data ingestion thật. |
| NautilusTrader | scaffold only | Adapter chỉ check import và simulation placeholder. |

## Missing features theo yêu cầu

- OpenBB ingestion lưu DuckDB/Parquet: missing.
- FinceptTerminal exportable analytics modules: missing.
- Qlib dataset builder thực tế: missing.
- Qlib experiment config/runner thật: scaffold only.
- Qlib signal export vào database: scaffold only.
- LEAN project generator/backtest runner thật: scaffold only.
- LEAN result parser portfolio metrics: scaffold only.
- Hummingbot order book/spread ingestion thực tế: missing.
- Hummingbot paper config đầy đủ cho bot thật: partial.
- Nautilus strategy generator/simulation runner thật: scaffold only.
- Freqtrade CLI result parser nối với batch runner: partial/missing integration.
- Freqtrade downloaded OHLCV import: missing.
- Best/worst pair or asset metrics: missing.
- Average profit metric riêng biệt: missing; hiện có `avg_win`, `avg_loss`.
- Separate fee-adjusted and slippage-adjusted metrics: partial; hiện gộp `fee_slippage_adjusted_return`.
- Out-of-sample thật theo time split/holdout: partial; fallback dùng nửa sau trade returns.
- Risk dry-run divergence: missing.
- Risk look-ahead runtime/static generated-code review integration: partial.
- Strategy status `archived`: model enum có, risk gate chưa dùng.
- `approved_for_dry_run`: config/model có, risk gate chưa bao giờ trả.
- Dashboard dry-run readiness chi tiết: partial.
- Dashboard missing-engine warnings chi tiết: partial.
- Tests cho optional engine behavior: missing.
- Tests cho safe defaults/live-trading absence: partial/missing.

