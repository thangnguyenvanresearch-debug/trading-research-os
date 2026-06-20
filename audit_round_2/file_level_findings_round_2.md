# Đánh giá chi tiết cấp tập tin Đợt 2 (File-level Findings Round 2)

Dưới đây là kết quả kiểm tra mã nguồn thực tế đối với từng tệp tin quan trọng trong đợt hardening pass.

---

### 1. [.gitignore](file:///D:/AI2/QuantGit/trading-research-os/.gitignore)
* **Kết quả kiểm tra:** Đã sửa lỗi (Fixed).
* **Chi tiết:** Bổ sung đầy đủ các quy tắc loại trừ các tệp tin sinh ra trong quá trình chạy (database, cache, data thô, reports, tệp cấu hình môi trường `.env`). Giữ lại cấu trúc thư mục rỗng thông qua `.gitkeep` bằng cách đảo ngược loại trừ phủ định dạng `!data/.gitkeep`.

---

### 2. [README.md](file:///D:/AI2/QuantGit/trading-research-os/README.md)
* **Kết quả kiểm tra:** Đã sửa lỗi (Fixed).
* **Chi tiết:** Tài liệu hướng dẫn rất đầy đủ, minh bạch và phân biệt rõ ràng các cấu phần đã chạy thực tế (v1 Freqtrade crypto path) và các cấu phần chỉ mang tính chất khung sườn phác thảo (LEAN, Qlib, Hummingbot, Nautilus). Bổ sung phần khắc phục sự cố chi tiết và trực diện.

---

### 3. [scripts/_bootstrap.py](file:///D:/AI2/QuantGit/trading-research-os/scripts/_bootstrap.py)
* **Kết quả kiểm tra:** Đã sửa lỗi (Fixed).
* **Chi tiết:** Đóng vai trò là tệp tin khởi chạy dùng chung cho mọi kịch bản. Thực hiện kiểm tra an toàn `assert_research_only(load_global_config())` ngay lúc nạp để chặn đứng mọi khả năng bật chế độ live trading ngoài ý muốn.

---

### 4. [src/core/validation.py](file:///D:/AI2/QuantGit/trading-research-os/src/core/validation.py)
* **Kết quả kiểm tra:** Đã sửa lỗi (Fixed).
* **Chi tiết:** Định nghĩa hàm `assert_research_only` để kiểm tra ranh giới an toàn (leverage, futures, live trading) và hàm `contains_forbidden_logic` chứa danh sách các từ khóa look-ahead nguy hiểm.

---

### 5. [src/core/models.py](file:///D:/AI2/QuantGit/trading-research-os/src/core/models.py)
* **Kết quả kiểm tra:** Đã sửa lỗi (Fixed).
* **Chi tiết:** Loại bỏ hoàn toàn quyền hoặc trạng thái `APPROVED_FOR_LIVE` khỏi `StrategyStatus` và `Permission`. Giới hạn cấp cao nhất là `APPROVED_FOR_DRY_RUN`.

---

### 6. [src/core/database.py](file:///D:/AI2/QuantGit/trading-research-os/src/core/database.py)
* **Kết quả kiểm tra:** Đã sửa lỗi (Fixed).
* **Chi tiết:** Hỗ trợ kiểm tra và tự động bổ sung cột (`_ensure_runtime_columns`) khi chạy trên cơ sở dữ liệu cũ để tránh sập luồng. Cơ chế hạ cấp tự động về SQLite hoạt động trơn tru nếu không cài đặt DuckDB.

---

### 7. [src/data_brain/freqtrade_data_adapter.py](file:///D:/AI2/QuantGit/trading-research-os/src/data_brain/freqtrade_data_adapter.py)
* **Kết quả kiểm tra:** Đã sửa lỗi (Fixed).
* **Chi tiết:** Tách biệt rõ ràng chế độ sinh dữ liệu mẫu (`--sample`, nguồn `sample_freqtrade_adapter`) và chế độ CLI thật (`--use-freqtrade-cli`, nguồn `freqtrade_cli_import`). CLI mode quét thực tế các tệp `.json`, `.json.gz`, và `.feather` trong thư mục Freqtrade và chuẩn hóa chúng về DuckDB/SQLite mà không tự động hạ cấp về sinh số liệu mẫu giả như trước.

---

### 8. [src/freqtrade_brain/batch_backtest_runner.py](file:///D:/AI2/QuantGit/trading-research-os/src/freqtrade_brain/batch_backtest_runner.py)
* **Kết quả kiểm tra:** Đã sửa lỗi (Fixed).
* **Chi tiết:** Chạy lệnh subprocess `freqtrade backtesting` thực tế với đầy đủ cấu hình đầu ra và nạp kết quả xuất ra vào bộ phân tích Parser. Luồng lỗi CLI ghi nhận rõ trạng thái thất bại thay vì sinh số liệu giả lập rỗng.

---

### 9. [src/freqtrade_brain/freqtrade_result_parser.py](file:///D:/AI2/QuantGit/trading-research-os/src/freqtrade_brain/freqtrade_result_parser.py)
* **Kết quả kiểm tra:** Đã sửa lỗi (Fixed).
* **Chi tiết:** Thiết kế Parser chuẩn hóa kết quả của Freqtrade, ánh xạ bí danh các cột chỉ số hiệu năng và trích xuất chỉ số hiệu quả ở cấp độ từng cặp giao dịch để tìm ra best/worst pair. Nếu thiếu các chỉ số sau hiệu chỉnh chi phí, hệ thống sao chép chỉ số thô và đưa ra cảnh báo `parser_warnings`.

---

### 10. [src/freqtrade_brain/freqtrade_strategy_converter.py](file:///D:/AI2/QuantGit/trading-research-os/src/freqtrade_brain/freqtrade_strategy_converter.py)
* **Kết quả kiểm tra:** Đã sửa lỗi (Fixed).
* **Chi tiết:** Dịch các đặc tả YAML thành lớp chiến thuật Python tương thích Freqtrade. Đảm bảo thuộc tính `can_short = False` và nạp đè phương thức `leverage` trả về giá trị cố định `1.0` để chặn rủi ro đòn bẩy/bán khống. Tệp đầu ra được ghi chính xác vào thư mục runtime `data/generated/freqtrade_strategies/`.

---

### 11. [src/risk_brain/risk_gate.py](file:///D:/AI2/QuantGit/trading-research-os/src/risk_brain/risk_gate.py)
* **Kết quả kiểm tra:** Đã sửa lỗi (Fixed).
* **Chi tiết:** Kiểm tra độ lệch dry-run so với backtest (`_dry_run_divergence_flags`), thực hiện quét mã nguồn spec và code sinh ra để loại bỏ rủi ro look-ahead (`_lookahead_review`), và áp dụng bộ quy tắc thăng cấp chiến thuật sang `approved_for_dry_run` rất khắt khe.

---

### 12. [src/risk_brain/overfit_detector.py](file:///D:/AI2/QuantGit/trading-research-os/src/risk_brain/overfit_detector.py)
* **Kết quả kiểm tra:** Đã sửa lỗi (Fixed).
* **Chi tiết:** Cảnh báo và từ chối các chiến thuật có đồ thị vốn quá mịn (`equity_smoothness` vượt ngưỡng `max_equity_curve_smoothness`), hoạt động đơn regime (`regime_count <= 1`), hoặc phụ thuộc quá nặng vào một cặp giao dịch duy nhất (`pair_concentration` vượt ngưỡng `max_pair_concentration`).

---

### 13. [src/decision_brain/decision_engine.py](file:///D:/AI2/QuantGit/trading-research-os/src/decision_brain/decision_engine.py)
* **Kết quả kiểm tra:** Đã sửa lỗi (Fixed).
* **Chi tiết:** Loại bỏ việc xóa quyết định cũ để tích lũy lịch sử. Quét các cặp giao dịch từ `pair_level_metrics` để sinh các bản ghi quyết định cụ thể cho từng cặp tiền thay vì mặc định hardcode cặp `BTC/USDT`.

---

### 14. [src/ai_strategy_brain/strategy_spec_validator.py](file:///D:/AI2/QuantGit/trading-research-os/src/ai_strategy_brain/strategy_spec_validator.py)
* **Kết quả kiểm tra:** Đã sửa lỗi (Fixed).
* **Chi tiết:** Thẩm định sâu miền giá trị dừng lỗ (`stop_loss` thuộc `(-0.50, 0.0)`), chốt lời (`take_profit` thuộc `(0.0, 1.0]`), giới hạn rủi ro tiếp xúc, và từ chối bất kỳ spec nào khai báo đòn bẩy hoặc tương lai.

---

### 15. [src/dashboard/streamlit_app.py](file:///D:/AI2/QuantGit/trading-research-os/src/dashboard/streamlit_app.py)
* **Kết quả kiểm tra:** Đã sửa lỗi (Fixed).
* **Chi tiết:** Ứng dụng Streamlit hiển thị rõ ràng nguồn dữ liệu thị trường, cảnh báo từ parser, engine provenance, trạng thái rủi ro chi tiết của Risk Gate, chẩn đoán các engine tùy chọn bị thiếu và an toàn 100% khi không chứa các thành phần điều khiển trực tiếp hoặc khởi động bot giao dịch.
