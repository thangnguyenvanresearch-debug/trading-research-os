# Remaining Local AI Issues

Không có critical/high/medium issues.

## Low

1. `allow_external_api: false` chưa được enforce trực tiếp

- File: `src/ai/local_ai_client.py`
- Hiện trạng: client chặn non-localhost khi `safe_mode=true`. Nếu người dùng cố tình đặt `safe_mode=false`, trường `allow_external_api:false` không tự chặn external endpoint.
- Tác động: thấp trong default config vì `safe_mode:true`.
- Fix đề xuất: reject non-localhost nếu `allow_external_api` không true, kể cả khi `safe_mode=false`.

2. Dashboard có thể chậm khi Ollama không chạy

- File: `src/dashboard/pages/12_local_ai_research.py`
- Hiện trạng: page load gọi `get_local_ai_status()`, endpoint local timeout tối đa khoảng 5 giây.
- Tác động: thấp; không phải safety issue.
- Fix đề xuất: cache status ngắn hạn hoặc thêm tùy chọn refresh status.

3. `_safe_fetch()` bắt broad exception

- File: `src/ai/research_engine.py`
- Hiện trạng: optional context fetch cho backtest/risk/decisions trả DataFrame rỗng với mọi exception.
- Tác động: thấp; có thể che lỗi query/schema trong audit/debug.
- Fix đề xuất: chỉ swallow missing-table errors, log warning cho lỗi khác.

## Not verifiable

Real local memo generation bằng Ollama chưa xác minh được vì Ollama không available tại thời điểm audit.
