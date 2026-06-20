# File-level findings

## `README.md`

- Implemented: mô tả purpose, architecture, setup, v1 workflow, engine roles, safety defaults, limitation.
- Partial: README nói external engines optional/adapters nhưng chưa ghi rõ phần nào là scaffold-only.
- Evidence: README lines 21-25 nêu Qlib/LEAN/Hummingbot/Nautilus ở các phase sau.

## `pyproject.toml`

- Issue: `duckdb` nằm trong dependencies bắt buộc, trong khi README nói fallback SQLite nếu DuckDB không installed.
- Risk: cài package sẽ kéo DuckDB, làm fallback ít ý nghĩa trong packaging.

## `.env.example`

- Safe: chỉ chứa cờ false và relative dirs, không thấy secret value.

## `configs/global.yaml`

- Safe: `live_trading_enabled`, `real_orders_enabled`, `leverage_enabled`, `futures_enabled` đều false.
- Partial: config an toàn có hàm `assert_research_only`, nhưng không thấy gọi bắt buộc trong script/dashboard.

## `configs/risk_rules.yaml`

- Implemented: có min trades, max drawdown, PF, OOS, concentration, smoothness, dry-run divergence threshold.
- Missing: `material_dry_run_divergence` có trong config nhưng không được dùng trong `risk_gate.py`.

## `database/schema.sql`

- Implemented: đủ bảng yêu cầu: assets, market_data, features, regimes, strategy_specs, generated_strategies, backtest_runs, backtest_metrics, risk_reviews, decisions, paper_trading_logs, engine_runs, experiment_notes.
- Partial: `backtest_metrics` không có best/worst pair, average profit tổng, fee và slippage tách riêng.

## `src/core/database.py`

- Good: DuckDB optional fallback SQLite; centralized connection; path từ config.
- Issue: `insert_dict()` build SQL table name bằng string caller truyền vào. Hiện callers nội bộ, nhưng nên giữ whitelist table names.
- Issue: broad optional import exception ở line 18 là chấp nhận được cho optional dependency, nhưng che giấu lỗi import khác.

## `src/core/validation.py`

- Implemented: forbidden token list có `shift(-`, `future_close`, `future_return`, `future_price`, `tomorrow`, `next_candle`, `lookahead`, leverage/futures true.
- Partial: đây là substring scan nông, không đủ phát hiện look-ahead trong code phức tạp hoặc spec lách qua naming khác.

## `src/ai_strategy_brain/strategy_spec_schema.py`

- Implemented: required fields và whitelist indicators/operators/engines.
- Partial: chưa dùng pydantic/jsonschema; chưa validate kiểu dữ liệu sâu hoặc bounds.

## `src/ai_strategy_brain/strategy_spec_validator.py`

- Implemented: reject missing fields, unsupported asset/engine, empty pairs, invalid indicator/operator, leverage/futures true, thiếu fee/slippage model.
- Issue: `float(risk.get("max_pair_exposure", 1))` có thể raise nếu input là string không numeric; không gom thành validation error.
- Missing: bounds cho stop_loss/take_profit/trailing/max_open_trades.

## `src/ai_strategy_brain/strategy_generator.py`

- Implemented: deterministic crypto templates, YAML output, registry insert.
- Partial: non-crypto chỉ trả một ETF placeholder, không generate đủ equity factor families.
- Issue: generated specs được ghi vào `src/ai_strategy_brain/generated_specs`, tức generated runtime artifacts nằm trong source tree.

## `src/freqtrade_brain/freqtrade_strategy_converter.py`

- Implemented: controlled YAML-to-Python template, embeds source YAML, `can_short = False`, leverage returns 1.0.
- Issue: import `numpy as np` trong generated strategy không dùng.
- Partial: converter chỉ support simple all/any flat logic, chưa support multi-timeframe thật.

## `src/freqtrade_brain/batch_backtest_runner.py`

- Implemented: internal fallback backtester, report JSON, DB metric storage.
- High issue: `_run_freqtrade_cli()` không export/parse result thật và trả `_empty_metrics()`.
- High issue: `except Exception` ở line 157 che nguyên nhân fetch/build failure.
- Issue: `regime_count` hardcode 2 trong fallback metrics.
- Issue: fee/slippage là hằng số `0.002`, chưa dùng fee/slippage model config.

## `src/freqtrade_brain/freqtrade_result_parser.py`

- Partial: parser map một số field Freqtrade.
- Missing: không parse out-of-sample, avg win/loss, pair concentration, fee/slippage adjusted, best/worst pair.
- Missing: không được gọi trong batch runner.

## `src/freqtrade_brain/dry_run_config_builder.py`

- Safe: `dry_run: True`, spot mode, API server disabled.
- Partial: chưa được dùng trong script/dashboard; config còn tối giản.

## `src/data_brain/freqtrade_data_adapter.py`

- Implemented: sample OHLCV generator, quality validation, DB ingest.
- High issue: khi dùng Freqtrade CLI vẫn ingest sample generated data, không đọc dữ liệu CLI tải về.

## `src/data_brain/openbb_adapter.py`

- Scaffold only: check import và trả placeholder.
- Safe: không có execution.

## `src/feature_brain/indicators.py`

- Implemented: EMA/SMA/RSI/ATR/Bollinger/MACD/returns/volatility/volume/drawdown/liquidity/spread proxy.
- Good: dùng rolling/ewm/current-past; không thấy negative shift.

## `src/feature_brain/regime_detector.py`

- Implemented: heuristic regime up/down/range, volatility buckets, breakout/mean-reversion/illiquid.
- Partial: confidence hardcode 0.70, không có validation theo historical labels.

## `src/risk_brain/risk_gate.py`

- Implemented: reject on drawdown, trades, PF, OOS, win/loss skew, fee/slippage adjusted return, overfit flags.
- Missing: dry-run divergence, look-ahead integration, `archived`, `approved_for_dry_run`.

## `src/decision_brain/strategy_score.py`

- Implemented: weights đúng gần yêu cầu 25/20/15/15/15/10.
- Partial: `regime_match` default True và không được tính từ spec/regime thật.

## `src/decision_brain/decision_engine.py`

- Implemented: emits signal, permission, score, regime, reasons, risk_flags.
- High issue: hardcode `"symbol": "BTC/USDT"`.
- High issue: `DELETE FROM decisions` làm mất lịch sử.
- Partial: explanations generic, không giải thích điều kiện entry cụ thể.

## `src/dashboard`

- Implemented: có app chính và 9 pages.
- Partial: nhiều page chỉ hiển thị dataframe/info; missing-engine warnings chưa đầy đủ; readiness dry-run chưa rõ.
- Safe: không thấy subprocess call trong dashboard.

## `src/lean_brain`

- Scaffold only: CLI status, project placeholder, converter skeleton, parser placeholder.

## `src/qlib_brain`

- Scaffold only: availability check và placeholder report/export.

## `src/hummingbot_brain`

- Partial/scaffold: spread, quote distance, inventory risk, arbitrage score, paper config.
- Safe: `paper_only: True`, `live_trading: False`.
- Missing: real order book ingestion/scanner connector.

## `src/nautilus_brain`

- Scaffold only: event dataclass, availability check, skeleton note, simulation placeholder.
- Safe: `live_enabled: False`.

## `scripts`

- Implemented: CLI workflow scripts exist.
- Issue: scripts write runtime data/specs/strategies/reports into project tree.
- Safe: no script found that places real orders.
- `scripts/launch_dashboard.py` uses subprocess to run Streamlit; acceptable script-side, not dashboard-side.

## `tests`

- Implemented: schema, no-lookahead substring, risk gate rejection, score range, data quality.
- Missing: safe defaults test, missing optional engine behavior, real/fallback backtest integration, result parser, dashboard smoke, full pipeline temp DB.

