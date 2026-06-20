# Các Vấn Đề Còn Tồn Tại (Remaining Issues)

Hệ thống đã giải quyết toàn bộ các lỗi nghiêm trọng (High/Critical) từ đợt đánh giá Đợt 1. Tuy nhiên, vẫn còn một số vấn đề ở mức độ Trung bình (Medium) và Thấp (Low) cần tiếp tục hoàn thiện trong các giai đoạn phát triển tiếp theo của dự án.

---

## 1. Các Engine tùy chọn khác vẫn là khung sườn (Scaffold-only)
* **Phân loại:** **Medium**
* **Tệp tin ảnh hưởng:**
  * `src/lean_brain/`
  * `src/qlib_brain/`
  * `src/nautilus_brain/`
  * `src/hummingbot_brain/`
  * `src/dashboard/pages/06_equity_lean_qlib.py`
  * `src/dashboard/pages/09_nautilus_future_engine.py`
* **Mô tả:** Các engine ngoài Freqtrade đều ở mức tích hợp giả lập cấu trúc (scaffold/placeholder) cho định hướng phát triển ở các Phase tiếp theo (Phase 3, 4, 5). Hiện tại, chúng chỉ trả về trạng thái hoạt động tĩnh thay vì chạy thực tế.
* **Mức độ ảnh hưởng:** Không ảnh hưởng đến luồng giao dịch Crypto Freqtrade của v1, nhưng người dùng sẽ không thể chạy backtest cổ phiếu hoặc các tính toán máy học phức tạp của Qlib ngay lúc này.
* **Khuyến nghị khắc phục:** Triển khai các adapter thực tế cho LEAN CLI, Qlib và Nautilus ở các đợt phát triển tiếp theo theo đúng kế hoạch của dự án.

---

## 2. Kiểm tra Look-ahead tĩnh bằng chuỗi con (Static Look-ahead Substring Checks)
* **Phân loại:** **Low**
* **Tệp tin ảnh hưởng:**
  * [validation.py](file:///D:/AI2/QuantGit/trading-research-os/src/core/validation.py)
  * [risk_gate.py](file:///D:/AI2/QuantGit/trading-research-os/src/risk_brain/risk_gate.py)
* **Mô tả:** Cơ chế phát hiện rò rỉ dữ liệu tương lai (look-ahead leak) vẫn dựa vào việc kiểm tra sự tồn tại của các từ khóa chuỗi con cụ thể (như `shift(-`, `future_close`, `tomorrow`, v.v.). Cơ chế này dễ bị bỏ qua nếu mã nguồn chiến thuật sinh ra viết các đoạn logic lách luật (ví dụ: gán biến trung gian, lặp ngược chuỗi, hoặc sử dụng các biến chỉ mục phức tạp).
* **Mức độ ảnh hưởng:** Thấp đối với các template chuẩn, nhưng có khả năng bị AI lách luật khi tự động sinh chiến thuật tùy ý.
* **Khuyến nghị khắc phục:** Xây dựng một bộ kiểm tra tĩnh dựa trên cây cú pháp trừu tượng (AST Analysis) để phân tích dòng chảy dữ liệu (data flow analysis) của các biến chỉ mục thời gian trong các biểu thức pandas.

---

## 3. Cơ sở dữ liệu DuckDB phụ thuộc cài đặt ngoài (Optional DuckDB Database dependency)
* **Phân loại:** **Low**
* **Tệp tin ảnh hưởng:**
  * [database.py](file:///D:/AI2/QuantGit/trading-research-os/src/core/database.py)
* **Mô tả:** Cơ chế lưu trữ tự động hạ cấp về SQLite nếu môi trường cục bộ thiếu thư viện `duckdb`. SQLite hoạt động rất tốt cho demo, nhưng sẽ gặp rào cản hiệu năng khi phân tích hàng triệu bản ghi factor trong tương lai.
* **Mức độ ảnh hưởng:** Nhẹ. Tài liệu đã ghi rõ cách khắc phục bằng lệnh cài đặt bổ sung `python -m pip install -e .[database]`.
* **Khuyến nghị khắc phục:** Nên in ra một thông báo cảnh báo rõ ràng trên console lúc khởi chạy script nếu phát hiện hệ thống đang chạy ở chế độ SQLite fallback.
