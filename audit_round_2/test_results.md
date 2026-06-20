# Kết Quả Kiểm Thử (Test Results)

Tất cả các bài kiểm thử đơn vị (unit tests) và tích hợp (integration tests) đã được chạy thành công trên Windows PowerShell bằng môi trường kiểm thử pytest.

## 1. Lệnh kiểm thử đã thực thi
```bash
python -m pytest -q
```

## 2. Tóm tắt kết quả
* **Số lượng bài test được thu thập (Collected):** 19
* **Số lượng bài test đã vượt qua (Passed):** 19
* **Số lượng bài test thất bại (Failed):** 0
* **Thời gian thực thi:** 3.17 giây
* **Kết quả:** `19 passed in 3.17s`

---

## 3. Danh sách các tệp kiểm thử đã xác minh
Dưới đây là chi tiết các bài kiểm thử nằm trong thư mục [tests/](file:///D:/AI2/QuantGit/trading-research-os/tests/) và nhiệm vụ xác minh tương ứng:

1. **[test_safe_defaults.py](file:///D:/AI2/QuantGit/trading-research-os/tests/test_safe_defaults.py)**
   * Xác minh không tồn tại quyền `APPROVED_FOR_LIVE` trong StrEnum.
   * Xác minh các giá trị mặc định trong `configs/global.yaml` tuyệt đối khóa tính năng live trading, leverage và futures.
2. **[test_data_quality.py](file:///D:/AI2/QuantGit/trading-research-os/tests/test_data_quality.py)**
   * Xác minh dữ liệu sinh ra bởi trình adapter vượt qua đầy đủ các kiểm tra chất lượng dữ liệu OHLCV.
3. **[test_freqtrade_data_adapter.py](file:///D:/AI2/QuantGit/trading-research-os/tests/test_freqtrade_data_adapter.py)**
   * Xác minh dữ liệu mẫu giả lập được dán nhãn nguồn `sample_freqtrade_adapter`.
   * Xác minh chế độ chạy CLI ném ngoại lệ rõ ràng, không tự động fallback khi thiếu tệp.
   * Xác minh việc chuẩn hóa dữ liệu từ tệp JSON bên ngoài được dán nhãn `freqtrade_cli_import`.
4. **[test_freqtrade_result_parser.py](file:///D:/AI2/QuantGit/trading-research-os/tests/test_freqtrade_result_parser.py)**
   * Xác minh bộ trích xuất kết quả Freqtrade CLI lấy đúng các trường hiệu năng, xác định cặp giao dịch tốt nhất/tệ nhất từ dữ liệu mock.
   * Xác minh bộ trích xuất đưa ra cảnh báo chuẩn khi thiếu các trường chỉ số phụ.
5. **[test_decision_engine.py](file:///D:/AI2/QuantGit/trading-research-os/tests/test_decision_engine.py)**
   * Xác minh quyết định được sinh ra riêng rẽ trên từng symbol (ví dụ: `ETH/USDT`, `SOL/USDT`).
   * Xác minh lịch sử quyết định được tích lũy đầy đủ và lưu trữ ổn định qua các lần chạy.
6. **[test_risk_gate.py](file:///D:/AI2/QuantGit/trading-research-os/tests/test_risk_gate.py)**
   * Xác minh cổng rủi ro từ chối (REJECTED) chiến thuật yếu kém (drawdown cao, ít giao dịch, v.v.).
   * Xác minh việc từ chối chiến thuật xảy ra sai lệch dry-run (dry-run divergence).
   * Xác minh việc từ chối chiến thuật dính rủi ro tương lai (look-ahead).
   * Xác minh việc thăng cấp chính xác chiến thuật lên `approved_for_dry_run` hoặc chuyển sang lưu trữ `archived`.
7. **[test_strategy_spec_schema.py](file:///D:/AI2/QuantGit/trading-research-os/tests/test_strategy_spec_schema.py)**
   * Xác minh spec validator từ chối các tham số rủi ro vượt ngưỡng (stop loss quá xa, take profit bất hợp lý).
   * Xác minh validator chặn các khai báo bật leverage hoặc futures.
8. **[test_no_lookahead.py](file:///D:/AI2/QuantGit/trading-research-os/tests/test_no_lookahead.py)**
   * Xác minh bộ lọc rò rỉ dữ liệu tương lai hoạt động tốt trên các từ khóa cấm.
9. **[test_optional_engines.py](file:///D:/AI2/QuantGit/trading-research-os/tests/test_optional_engines.py)**
   * Xác minh các engine phụ (LEAN, Qlib, OpenBB, Nautilus) hoạt động an toàn ở chế độ giả lập cấu trúc mà không gây crash cho hệ thống chính.
10. **[test_full_fallback_pipeline.py](file:///D:/AI2/QuantGit/trading-research-os/tests/test_full_fallback_pipeline.py)**
    * Chạy kiểm thử tích hợp cuối-cuối (End-to-End) mô phỏng toàn bộ luồng hoạt động: Sinh dữ liệu mẫu -> Tính đặc trưng -> Sinh đặc tả YAML -> Dịch mã nguồn chiến thuật -> Chạy backtest fallback -> Đánh giá rủi ro -> Lưu quyết định vào DB tạm thời. Tất cả các bước đều hoàn thành trơn tru.
