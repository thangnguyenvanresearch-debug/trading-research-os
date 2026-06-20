# Remaining LEAN Issues

## Low / Future Work

1. **Executable LEAN backtest chưa được xác minh**

- Evidence: `get_lean_status()` trả `lean_cli_available=false`.
- Impact: integration hiện mới xác minh data export, skeleton, unavailable path, DB/report recording. Chưa thể khẳng định generated project chạy thành công trong LEAN CLI.
- Fix: cài LEAN CLI local, giữ cloud/broker disabled, chạy `python scripts/run_lean_backtest.py ...`, audit lại output và metrics parser.

2. **Generated skeleton dùng `SetHoldings()`**

- Evidence: `data/generated/lean/projects/.../Main.py` có `self.SetHoldings(symbol, weight)`.
- Impact: trong LEAN backtest, đây là API portfolio allocation/backtest. Không phải real broker order vì không có live/broker config. Tuy nhiên đây vẫn là lệnh giao dịch trong simulation, nên cần giữ nhãn local backtest và audit lại trước khi bật bất kỳ execution nào.
- Fix: tiếp tục giữ research-only. Nếu muốn giảm ambiguity, có thể tạo skeleton analytics-only hoặc paper portfolio simulator trước khi gọi LEAN order APIs.

## No Critical / High / Medium Issues

Không phát hiện issue critical, high, hoặc medium trong phạm vi audit này.

