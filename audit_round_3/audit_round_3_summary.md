# Tóm tắt audit Round 3

## Verdict

**Trạng thái:** accepted

**Điểm Round 2:** 8.8 / 10  
**Điểm Round 3:** 9.1 / 10

Round 3 remediation được chấp nhận. Các mục còn lại từ Round 2 đã được xử lý đúng trọng tâm: bổ sung AST look-ahead analysis, cảnh báo SQLite fallback rõ ràng, và chuẩn hóa diagnostic cho optional engines. Không phát hiện thay đổi nào bật live trading, futures, leverage, real orders, hoặc API key/secret handling.

## Kết quả chính

- **AST look-ahead:** fixed. Có `ast` analysis trong `src/core/validation.py`, phát hiện negative `.shift()`, future `.iloc[index + n]`, future-looking identifiers, và không execute/import generated strategy.
- **Risk gate integration:** fixed. `src/risk_brain/risk_gate.py` dùng substring + AST review cho generated strategy code, thu thập `spec_path` và `code_path`.
- **SQLite fallback warning:** fixed. `src/core/database.py` log warning rõ ràng khi DuckDB unavailable, hướng dẫn `pip install -e .[database]`, và test xác nhận warning chỉ một lần/process.
- **Optional engine diagnostics:** fixed/mostly fixed. Có status object chuẩn với `safe_for_live: false`; dashboard dùng các status này. FinceptTerminal vẫn chỉ là config/README “mentioned only”, chưa có adapter riêng.
- **Dashboard honesty:** fixed. Dashboard hiển thị engine status, capability, next step, safe_for_live false; không thấy live/order controls.
- **Tests:** pass. `27 passed in 6.59s` trong lần chạy audit.

## Top remaining issues

1. **Low:** Test suite chưa có test pytest riêng cho `shift(periods=-1)`, dù kiểm tra ad-hoc xác minh analyzer bắt được pattern này.
2. **Low:** `_lookahead_review()` trả `inspected_paths`, nhưng `run_risk_reviews()` chưa ghi đường dẫn đã inspect vào `risk_reviews.flags`; khi có lỗi, flag hiện chỉ ghi pattern, chưa ghi file path liên quan.
3. **Low / planned:** Optional engines ngoài Freqtrade vẫn scaffold/future theo kế hoạch. Đây không phải regression và không ảnh hưởng v1 crypto research path.
4. **Low:** `configs/engine_registry.yaml` dùng status `mentioned_only` cho FinceptTerminal, không nằm trong `ALLOWED_ENGINE_STATUSES` của code-level optional engine status. Cách ghi này trung thực, nhưng status taxonomy chưa hoàn toàn đồng nhất.

## Safety

Dự án vẫn **an toàn cho local research/demo**. Không chạy real exchange-connected workflow trong audit. Không phát hiện live trading/futures/leverage/real-order capability mới.

