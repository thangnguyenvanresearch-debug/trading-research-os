# Đánh giá lỗi hồi quy (Regression Check)

Sau khi kiểm tra toàn bộ thay đổi mã nguồn trong đợt hardening pass thứ 2, chạy biên dịch tĩnh và thực hiện toàn bộ 19 bài kiểm thử tích hợp/đơn vị, kết luận như sau:

**KHÔNG PHÁT HIỆN BẤT KỲ LỖI HỒI QUY NÀO (NO REGRESSIONS DETECTED)**

### Các chỉ số kiểm tra:
1. **Lỗi biên dịch:** `python -m compileall src scripts -q` hoàn thành thành công mà không xuất ra bất kỳ thông báo lỗi hoặc cảnh báo cú pháp nào.
2. **Kiểm thử đơn vị và tích hợp:** `python -m pytest -q` thu thập và chạy thành công 19/19 bài test. Các bài test kiểm thử đường dẫn dữ liệu lỗi, rủi ro tương lai, độ lệch dry-run và kịch bản thăng cấp đều vượt qua trơn tru mà không làm gián đoạn luồng làm việc.
3. **Chạy thử nghiệm luồng công việc (E2E Dry-run):**
   * Cơ sở dữ liệu khởi tạo chính xác.
   * Dữ liệu giả lập được sinh đúng chuẩn và nạp vào DB.
   * Chiến thuật YAML được sinh và dịch thành mã Freqtrade tương thích hoàn hảo.
   * Tiến trình backtest fallback nội bộ chạy và ghi nhận kết quả đầy đủ mà không gây treo hệ thống hay lỗi chia cho 0.
   * Bộ chấm điểm chiến thuật hoạt động đúng kỳ vọng, ghi nhận lịch sử vào bảng quyết định.

### Các thay đổi được đảm bảo an toàn:
* Cơ chế tự động thêm cột bị thiếu trong cơ sở dữ liệu (`_ensure_runtime_columns`) giúp ngăn ngừa sự cố sập luồng do không khớp phiên bản DB khi chạy các script kiểm tra trên cơ sở dữ liệu cũ.
* Cơ chế hạ cấp SQLite tự động khi thiếu DuckDB đảm bảo ứng dụng hoạt động ổn định trên mọi môi trường retail thông thường.
* Mã nguồn chiến thuật sinh ra được ghi vào đúng thư mục `data/generated/` thay vì ghi đè gây rối thư mục mã nguồn `src`.
