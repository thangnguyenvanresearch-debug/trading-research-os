# Remaining LEAN CLI Patch Issues

## Medium/High/Critical

Không phát hiện issue critical, high, hoặc medium.

## Low

1. **Executable LEAN backtest vẫn chưa verified**

- Evidence: `lean_bt_f4d0947fa6ef` failed do timeout sau 900 giây.
- Impact: Chưa thể claim LEAN executable local backtest hoạt động end-to-end.
- Fix practical: tạo phase riêng cho Docker/LEAN runtime diagnostics, image pull/cache, project layout/data format, và parser real result.

2. **Docker status helper chưa phân biệt CLI và daemon**

- Evidence: `get_lean_status()` báo `docker_available=True` vì `shutil.which("docker")`, nhưng `docker info` fail do daemon unavailable.
- Impact: Dashboard/status có thể hơi lạc quan về khả năng chạy executable LEAN.
- Fix practical: đổi thành `docker_cli_available` và thêm `docker_daemon_available` bằng bounded `docker info` check.

3. **Visual dashboard chưa verified**

- Evidence: HTTP check `localhost:8501` failed vì Streamlit không chạy.
- Impact: Không xác minh trực quan page 14 trong audit này.
- Fix practical: start Streamlit thủ công rồi kiểm page `14_lean_backtests`.

## Future Work

- LEAN executable runtime diagnostics.
- Qlib integration phase.
- Nếu cần LEAN thật, xác minh Docker image/runtime riêng mà không dùng `lean init`, `lean login`, cloud credentials, brokerage, live trading.
