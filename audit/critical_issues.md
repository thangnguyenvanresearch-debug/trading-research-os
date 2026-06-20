# Critical and high-priority issues

## Critical

Không phát hiện critical issue dựa trên file đã kiểm tra. Không thấy live trading mặc định, real order placement, futures/leverage mặc định, hoặc secret pattern rõ ràng.

## High

### 1. Freqtrade CLI backtest path chưa tạo metrics thật

- Evidence: `src/freqtrade_brain/batch_backtest_runner.py:192-197`
- Code gọi command `["freqtrade", "backtesting", "--strategy", spec["strategy_name"]]`.
- Sau khi CLI thành công, function trả `_empty_metrics()` kèm note `"parse concrete result export in phase 1 hardening"`.
- Vì sao quan trọng: người dùng có thể tưởng đã backtest bằng Freqtrade thật, nhưng database nhận metrics rỗng/giả.
- Fix thực tế: truyền `--userdir`, `--config`, strategy class name đúng, `--export trades`, `--export-filename`; sau đó parse JSON export bằng parser chuẩn và lưu metrics thật.

### 2. Freqtrade data adapter không import dữ liệu Freqtrade thật

- Evidence: `src/data_brain/freqtrade_data_adapter.py:110-120`
- Nếu `--use-freqtrade-cli` được bật, code gọi downloader rồi vẫn sinh `generate_sample_ohlcv(...)` cho từng pair.
- Vì sao quan trọng: backtest có thể chạy trên data giả dù người dùng nghĩ đã dùng exchange data.
- Fix thực tế: tách `--sample` khỏi `--use-freqtrade-cli`; khi dùng CLI, đọc file OHLCV từ `user_data/data/...`, normalize, validate, ingest.

### 3. Risk gate thiếu một số tiêu chí bắt buộc

- Evidence: `src/risk_brain/risk_gate.py:12-35`
- Có drawdown, trade count, profit factor, OOS, win/loss, fee/slippage adjusted, overfit flags.
- Thiếu: dry-run divergence, possible look-ahead bias runtime check, archived status workflow, approved_for_dry_run promotion logic.
- Vì sao quan trọng: tiêu chí acceptance yêu cầu reject nếu backtest/dry-run diverge, dùng future info, và có các status đầy đủ.
- Fix thực tế: thêm inputs từ `paper_trading_logs`, generated code/spec audit result, dry-run metrics; implement `archived` và rule rõ cho `approved_for_dry_run`.

### 4. Decision engine hardcode symbol và xóa lịch sử

- Evidence: `src/decision_brain/decision_engine.py:24`, `src/decision_brain/decision_engine.py:44`
- `DELETE FROM decisions` xóa toàn bộ history; `"symbol": "BTC/USDT"` gán cố định.
- Vì sao quan trọng: hệ thống multi-pair không thể phát quyết định đúng theo từng symbol, và không giữ strategy history đúng yêu cầu.
- Fix thực tế: emit decision theo pair/spec/backtest pair metrics; lưu append-only hoặc versioned decisions; chỉ mark stale nếu cần.

### 5. Không thấy `.gitignore`, artifact runtime nằm trong workspace

- Evidence: lệnh đọc `.gitignore` không trả file; workspace có `database/trading_os.duckdb`, `data/features/*.csv`, `data/processed/*.csv`, `reports/freqtrade/*.json`, `__pycache__`.
- Vì sao quan trọng: dễ commit nhầm data/report/cache/runtime DB; có thể lộ dữ liệu nghiên cứu hoặc làm repo phình lớn.
- Fix thực tế: thêm `.gitignore` cho `.env`, `data/**`, `database/*.duckdb`, `reports/**`, `__pycache__/`, `.pytest_cache/`, trừ `.gitkeep` nếu cần giữ folder.

