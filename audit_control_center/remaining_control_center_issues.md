# Remaining Control Center Issues

## Critical / High

Không phát hiện critical hoặc high issue.

## Medium

Không có medium issue bắt buộc, nhưng có một accuracy issue đáng sửa sớm nếu dashboard dùng cho người không kỹ thuật.

## Low / Accuracy

1. **LEAN readiness bị overstate**

- Evidence: `get_latest_engine_statuses()` trả `"lean": {"status": "ready", "cli": true}`.
- Reality: executable LEAN backtest vẫn chưa verified; run `lean_bt_f4d0947fa6ef` failed timeout.
- Fix: đổi status card thành `cli_detected_executable_unverified` hoặc thêm field `executable_verified: false`, `latest_executable_status: failed_timeout`.

2. **Daily Scheduler status không query Windows Task Scheduler**

- Evidence: helper lấy latest row từ `daily_research_runs`.
- Reality: không gọi `Get-ScheduledTask`.
- Fix: đổi label thành `latest_daily_run` hoặc thêm status riêng `scheduler_state: not verified`.

3. **CLI report không hoàn toàn DB read-only**

- Evidence: `scripts/report_control_center_status.py` gọi `initialize_database()`.
- Impact: có thể tạo schema nếu DB trống.
- Fix: nếu muốn strict read-only, không init DB trong report script; hoặc document là “schema initialization only, no research data mutation”.

4. **Warning/error summaries chưa truncate**

- Evidence: queries select raw `warnings_json` / `errors_json`.
- Impact: dashboard/report có thể bị ồn nếu lỗi dài.
- Fix: truncate display summaries, giữ full JSON trong expander/detail.

5. **README Control Center section thiếu caveat rõ về LEAN/Qlib**

- Evidence: Control Center section nói overview, nhưng không nêu riêng LEAN executable unverified/Qlib trainer missing.
- Fix: thêm hai dòng caveat trong section.

6. **Dashboard visual not verified**

- Evidence: `localhost:8501` refused connection.
- Fix: start Streamlit and manually inspect page `00_research_control_center`.
