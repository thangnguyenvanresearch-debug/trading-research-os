# Tóm tắt audit

**Kết luận:** dự án là một skeleton v1 có hướng kiến trúc đúng, nhưng chưa phải một Multi-Brain Trading Research OS hoàn chỉnh. Phần chạy được nhất là pipeline crypto nội bộ: sample data -> features -> YAML specs -> Freqtrade-compatible strategy code -> fallback backtest -> risk review -> decision/dashboard. Các engine còn lại hầu hết là scaffold.

**Điểm tổng:** 5.8 / 10.

**Không phát hiện:** secret pattern dạng `api_key`, `secret`, `token`, `password`, `private_key` trong các file nhỏ được quét. Không thấy trạng thái live trading được bật mặc định.

**Vấn đề lớn nhất:**

1. Freqtrade CLI backtest chưa thật sự dùng/parse kết quả Freqtrade. File `src/freqtrade_brain/batch_backtest_runner.py` gọi `freqtrade backtesting --strategy ...` nhưng không có userdir/config/export và trả `_empty_metrics()`.
2. `src/data_brain/freqtrade_data_adapter.py` luôn sinh sample OHLCV sau bước optional download; dữ liệu Freqtrade tải thật không được import.
3. Risk gate còn thiếu dry-run divergence, look-ahead runtime review, `archived`, và logic promote `approved_for_dry_run`.
4. Decision engine hardcode `BTC/USDT` và xóa toàn bộ bảng decisions mỗi lần build.
5. Không thấy `.gitignore`; trong workspace có database DuckDB, CSV features, reports và `__pycache__`. Trạng thái có bị commit hay không: **Không xác minh được** vì thư mục không phải git repo.

**Trạng thái repo/tool:**

| Tool | Trạng thái |
|---|---|
| OpenBB | scaffold only |
| FinceptTerminal | mentioned only |
| Qlib | scaffold only |
| LEAN | scaffold only |
| Freqtrade | partially implemented |
| Hummingbot | partially implemented/scaffold only |
| NautilusTrader | scaffold only |

**Ưu tiên sửa:** làm Freqtrade data/backtest path thật trước, rồi tăng risk gate và decision engine. Sau đó mới mở rộng LEAN/Qlib/OpenBB.

