# Gợi ý cải thiện mã nguồn cho Codex (Codex Fix Prompt Round 2)

Dưới đây là prompt gợi ý để Codex tối ưu hóa các điểm chưa hoàn thiện nhỏ còn lại của hệ thống:

```text
Hãy thực hiện cải tiến mã nguồn cho dự án Trading Research OS tại 2 tệp tin sau:

1. Nâng cấp bộ lọc look-ahead tĩnh trong src/core/validation.py:
- Hiện tại, hàm contains_forbidden_logic sử dụng so khớp chuỗi con đơn giản (substring matching) với danh sách FORBIDDEN_STRINGS. Hãy viết thêm cơ chế phân tích cây cú pháp trừu tượng (AST Analysis) của Python để quét qua mã nguồn của các chiến thuật được sinh ra (generated strategy code).
- Phát hiện các mẫu truy cập dữ liệu tương lai dạng dataframe['close'].shift(-N) với N > 0, dataframe.iloc[index + N], các chỉ mục tương lai hoặc việc sử dụng chỉ mục vòng lặp lùi làm rò rỉ dữ liệu của nến tiếp theo.
- Kết hợp cả hai phương pháp (kiểm tra chuỗi con và phân tích AST) để đưa ra danh sách cảnh báo đầy đủ nhất.

2. Bổ sung cảnh báo SQLite Fallback trong src/core/database.py:
- Khi nạp module database.py, nếu thư viện duckdb không tồn tại (Exception được bắt), hãy in một thông báo cảnh báo rõ ràng ra console bằng logger (logger.warning) để người dùng biết rằng hệ thống đang hạ cấp xuống sử dụng SQLite làm bộ nhớ lưu trữ thay vì DuckDB.
- Thông báo cảnh báo cần hướng dẫn người dùng chạy lệnh cài đặt DuckDB: "Để cài đặt DuckDB làm cơ sở dữ liệu phân tích chuẩn, hãy chạy: pip install -e .[database]"

Hãy thực hiện chỉnh sửa trực tiếp và đảm bảo toàn bộ bộ kiểm thử pytest vẫn vượt qua thành công.
```
