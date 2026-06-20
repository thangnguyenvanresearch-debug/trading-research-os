# Báo cáo audit đầy đủ

## Phạm vi và phương pháp

Audit được thực hiện ở chế độ chỉ đọc source và chỉ ghi file vào `D:\AI2\QuantGit\trading-research-os\audit`. Các file đã kiểm tra gồm README, pyproject, `.env.example`, configs, schema, scripts, modules trong `src/`, generated specs/strategies, tests và artifact hiện diện trong workspace.

Không chạy script live trading, không chạy bot, không kết nối exchange, không cài package. Không chạy pytest trong audit này để tránh tạo thêm file ngoài `audit`. Trạng thái test pass tại thời điểm audit: **Không xác minh được**. Tests được đọc tĩnh.

Thư mục không phải git repo; lệnh `git status --short` trả lỗi. Do đó trạng thái file nào đã commit hay chưa: **Không xác minh được**.

## 1. Architecture audit

### Kết luận

**Partially implemented.** Cấu trúc thư mục khớp khá tốt với kiến trúc Multi-Brain: `core`, `data_brain`, `feature_brain`, `ai_strategy_brain`, `freqtrade_brain`, `lean_brain`, `qlib_brain`, `hummingbot_brain`, `nautilus_brain`, `risk_brain`, `decision_brain`, `registry`, `dashboard`.

### Điểm tốt

- Module separation theo brain rõ ràng.
- Config nằm trong `configs/`.
- Paths dùng `src/core/paths.py`, không thấy hardcoded absolute `D:\...` trong source.
- Optional engines chủ yếu fail gracefully bằng availability checks hoặc placeholder returns.

### Vấn đề

- Nhiều brain chỉ là scaffold. LEAN/Qlib/Nautilus gần như chưa có pipeline thật.
- Coupling trực tiếp vào database ở nhiều module qua `fetch_dataframe`, `insert_dict`, `execute`.
- Runtime/generated artifacts nằm trong source tree: `src/ai_strategy_brain/generated_specs`, `src/freqtrade_brain/generated_strategies`.
- `decision_engine.py` xóa toàn bộ decision history và hardcode symbol.
- Có `__pycache__`, `.pytest_cache`, data CSV, DuckDB và reports trong workspace.

## 2. Repository leverage audit

| Tool | Trạng thái | Nhận xét |
|---|---|---|
| OpenBB | scaffold only | `openbb_adapter.py` chỉ check import và trả placeholder context. Không ingest data. Không execution. |
| FinceptTerminal | mentioned only | Có role trong `engine_registry.yaml` và README, không có module/code. |
| Qlib | scaffold only | Availability check, placeholder experiment/report/export. Không dataset conversion thật. |
| LEAN | scaffold only | CLI status, project placeholder, skeleton converter có `pass`, parser placeholder. |
| Freqtrade | partially implemented | Có YAML converter, generated strategies, fallback backtester, dry-run config builder. CLI path chưa parse kết quả thật. |
| Hummingbot | partially implemented/scaffold only | Có spread/arbitrage/inventory functions và paper config. Không có Hummingbot connector/order book ingestion thật. |
| NautilusTrader | scaffold only | Event dataclass, availability check, simulation placeholder. Không required cho v1. |

Không thấy engine nào bật live execution mặc định.

## 3. Strategy safety audit

### Implemented

- YAML-first strategy generation trong `strategy_generator.py`.
- Required fields trong `strategy_spec_schema.py`: `strategy_name`, `asset_class`, `engine_target`, `timeframe`, `pairs`, `strategy_type`, `regime_fit`, `entry_logic`, `exit_logic`, `risk`, `validation`.
- Validator kiểm tra allowed asset/engine/indicator/operator.
- Validator reject `risk.leverage_allowed` và `risk.futures_allowed` nếu không phải false.
- Generated Freqtrade code embed source YAML trong docstring và có comment traceability.
- Generated strategies có `can_short = False` và `leverage()` trả `1.0`.

### Partial/Missing

- Look-ahead check chỉ là substring scan trong `core/validation.py`; chưa có AST/static code audit sâu.
- Validator chưa enforce bounds cho stop loss/take profit/max trades/exposure ngoài `max_pair_exposure <= 1`.
- Không có JSONSchema/Pydantic model typed.
- AI local LLM chưa tích hợp; generator hiện deterministic templates. Điều này an toàn nhưng chưa phải AI strategy brain hoàn chỉnh.

## 4. Backtesting audit

### Implemented

- Fallback internal backtester trong `freqtrade_brain/batch_backtest_runner.py`.
- Backtest reports lưu JSON vào `reports/freqtrade`.
- Metrics lưu vào `backtest_metrics`.
- Standard metrics hiện có: total return, out-of-sample return, max drawdown, sharpe, sortino, win rate, trade count, profit factor, avg win/loss, fee_slippage_adjusted_return, pair_concentration, regime_count, equity_smoothness.

### High issues

- Freqtrade CLI path chưa thật: `_run_freqtrade_cli()` chỉ chạy command tối giản và trả `_empty_metrics()`.
- `freqtrade_result_parser.py` không được batch runner dùng.
- Data adapter không import actual Freqtrade downloaded files.

### Scaffold only

- LEAN backtest path: scaffold only.
- Qlib experiment path: scaffold only.
- Hummingbot scanner/paper lab: partial functions, chưa có real order book ingestion.
- Nautilus simulation adapter: scaffold only.

## 5. Risk gate audit

### Implemented

`risk_gate.py` reject theo:

- max drawdown
- trade count
- profit factor
- out-of-sample result
- high win rate but larger average loss
- fee/slippage-adjusted return
- pair concentration
- one-regime behavior
- suspicious equity smoothness

### Missing

- dry-run vs backtest divergence.
- possible look-ahead bias check integrated into risk review.
- status `archived` trong risk gate.
- status `approved_for_dry_run` không bao giờ được trả bởi `review_metrics()`.

Không thấy `approved_for_live` trong code/config được quét.

## 6. Decision brain audit

### Implemented

- Score 0-100 trong `strategy_score.py`.
- Weights đúng gần yêu cầu: 25% OOS, 20% drawdown, 15% return quality, 15% trade count, 15% regime fit, 10% cost robustness.
- Output có signal, permission, score, regime, reasons, risk_flags.
- Permissions không có `APPROVED_FOR_LIVE`.

### Issues

- `decision_engine.py` hardcode `"symbol": "BTC/USDT"`.
- `decision_engine.py` xóa bảng decisions bằng `DELETE FROM decisions`.
- Regime fit không được match thật với `strategy_specs.regime_fit`; `score_strategy()` được gọi default `regime_match=True`.
- Explanations generic, không giải thích trigger cụ thể của entry/exit logic.

## 7. Dashboard audit

### Implemented

Có đủ 9 page:

- Market Cockpit
- Strategy Factory
- Backtest Leaderboard
- Risk Gate
- Crypto Freqtrade
- Equity LEAN + Qlib
- Market Making Lab
- Arbitrage Scanner
- Nautilus Future Engine

Dashboard chính có decision cockpit, latest signal, leaderboard, safety defaults. Market page có chart, regime, latest decision.

### Partial

- Equity LEAN + Qlib page chỉ hiển thị status/placeholder.
- Market Making/Arbitrage page chỉ dùng input mẫu, chưa đọc live/paper scanner logs.
- Missing engine warnings còn rất đơn giản.
- Dry-run readiness chưa có panel rõ ràng.
- Rejected strategy explanation hiển thị được flags nhưng chưa drilldown theo test/OOS/pair.

Không thấy subprocess trong dashboard modules.

## 8. Data/database audit

### Implemented

- Database schema đủ bảng yêu cầu.
- Data folders có raw/processed/features/openbb/freqtrade/lean/qlib/hummingbot/nautilus.
- Data quality checks có basic OHLCV validation.
- Paths config-driven tương đối, không thấy hardcoded absolute path trong source.

### Issues

- `database/trading_os.duckdb` hiện có trong workspace.
- `data/processed/*.csv`, `data/features/*.csv`, `reports/freqtrade/*.json` hiện có trong workspace.
- Không thấy `.gitignore`; trạng thái commit: **Không xác minh được** vì không phải git repo.
- Sample data là default, dễ gây hiểu nhầm nếu không ghi rõ trong CLI output.

## 9. Security audit

### Không phát hiện

- Không thấy secret pattern dạng `api_key`, `secret`, `token`, `password`, `private_key` trong file nhỏ được quét.
- `.env.example` không chứa secret.
- Live trading/futures/leverage mặc định false.
- Không thấy real order placement/default live market making.
- Dashboard không chạy shell/subprocess.

### Risks

- `.gitignore` missing.
- Generated/runtime artifacts trong project tree.
- `insert_dict()` nhận table name string; hiện internal-only nhưng nên whitelist.
- Broad exceptions có thể che lỗi quan trọng (`batch_backtest_runner.py`, `openbb_adapter.py`, `csv_parquet_loader.py`).

## 10. Code quality audit

### Điểm tốt

- Module nhỏ, dễ đọc.
- Type hints khá nhiều.
- Có docstring ở một số entrypoints.
- Config loader/path helpers đơn giản.

### Vấn đề

- Duplicate indicator logic giữa feature brain và generated Freqtrade template.
- Broad `except Exception` trong path quan trọng.
- Dead import `numpy as np` trong generated strategies.
- Placeholder nhiều nhưng chưa được đánh dấu bằng interface contracts/test rõ.
- Một số workflow assumption hardcoded: generated specs trong `src`, symbol BTC/USDT, sample data default.

## 11. Test audit

### Implemented tests

- Strategy spec schema generated specs valid.
- No negative shift in generated strategy string.
- Risk gate rejects weak strategy.
- Score range 0-100.
- Sample data quality.

### Missing tests

- Safe defaults/no live permission.
- Optional engine missing behavior.
- Full v1 pipeline with temp database.
- Freqtrade result parser fixture.
- Freqtrade CLI path behavior mocked.
- Decision engine non-hardcoded symbols and history preservation.
- Risk gate dry-run divergence.
- Dashboard smoke import/page tests.

## 12. Documentation audit

README covers:

- Project purpose.
- Architecture.
- Role of each repo.
- Setup.
- Run v1.
- Add strategy templates.
- Backtests/scoring.
- Dashboard.
- Safety defaults.
- Limitations and overfitting warning.
- Live trading disabled by default.

Missing/partial:

- Chưa phân biệt đủ rõ trong README rằng OpenBB/Qlib/LEAN/Hummingbot/Nautilus đang scaffold-only.
- Chưa cảnh báo mạnh rằng sample synthetic data là default.
- Chưa có troubleshooting cho missing engines.

## Overall verdict

Dự án hiện là một v1 skeleton có pipeline demo local hoạt động về mặt cấu trúc, nhưng chưa đạt mức “multi-engine quant research OS” thực tế. Điểm mạnh là safety-first YAML spec pipeline và dashboard shell. Điểm yếu chính là backtest/data path thật chưa hoàn chỉnh, các engine ngoài Freqtrade chỉ scaffold, và risk/decision history chưa đủ nghiêm túc.

Ưu tiên sửa không phải thêm engine mới, mà là làm Freqtrade data/backtest path trung thực, tăng risk gate, và sửa decision engine để support multi-symbol/history.

