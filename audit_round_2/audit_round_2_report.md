# Báo Cáo Đánh Giá Code Toàn Diện Đợt 2 (Round 2 Audit Report)

## 1. Phạm vi đánh giá (Scope)
Đợt đánh giá này tập trung vào việc kiểm tra sự chính xác và an toàn của các bản sửa lỗi (fixes) được tuyên bố sau đợt hardening pass đầu tiên, bao gồm:
* Vệ sinh repo và cấu hình an toàn mặc định (.gitignore, chế độ research-only).
* Luồng nhập dữ liệu Freqtrade (phân tách rõ ràng giữa chế độ `--sample` và tải dữ liệu thật từ CLI).
* Cơ chế chạy backtest Freqtrade CLI (không trả về chỉ số giả lập rỗng, hỗ trợ tách biệt đường dẫn sinh code).
* Bộ phân tích kết quả Freqtrade (result parser).
* Engine đưa ra quyết định (Decision Engine) phân tách theo từng cặp giao dịch và lưu giữ lịch sử.
* Cổng rủi ro (Risk Gate) hỗ trợ đánh giá dry-run divergence, look-ahead risk, và quản lý các trạng thái archived/approved_for_dry_run.
* Thẩm định cấu trúc chiến thuật (Strategy Spec Validation).
* Vị trí lưu trữ các chiến thuật được sinh ra trong thư mục `data/generated/...`.
* Bảng điều khiển dashboard hiển thị nguồn gốc dữ liệu, cảnh báo của bộ phân tích, và chẩn đoán các engine bị thiếu.
* Kiểm thử (Testing) và tài liệu hướng dẫn (Documentation).

---

## 2. Các lệnh đã thực thi (Commands Run)
Để xác minh độ tin cậy của mã nguồn, các lệnh an toàn sau đã được thực thi và đều vượt qua (passed):
1. Khởi tạo cơ sở dữ liệu dự phòng SQLite:
   `python scripts/init_database.py`
2. Sinh dữ liệu mẫu xác định (deterministic sample data) cho BTC/USDT và ETH/USDT:
   `python scripts/download_crypto_data.py --sample --pairs BTC/USDT ETH/USDT --timeframe 1h`
3. Tính toán các đặc trưng kỹ thuật:
   `python scripts/build_features.py`
4. Sinh 3 bản đặc tả chiến thuật YAML:
   `python scripts/generate_strategy_specs.py --asset-class crypto --count 3`
5. Chuyển đổi các đặc tả YAML thành lớp chiến thuật Freqtrade tương thích:
   `python scripts/convert_specs_to_freqtrade.py`
6. Chạy thử nghiệm backtest thông qua chế độ fallback nghiên cứu cục bộ:
   `python scripts/run_freqtrade_backtests.py`
7. Chạy chấm điểm chiến thuật và lưu kết quả đánh giá rủi ro cùng quyết định giao dịch vào DB:
   `python scripts/score_strategies.py`
8. Chạy toàn bộ bộ kiểm thử đơn vị và tích hợp:
   `python -m pytest -q`
9. Biên dịch tĩnh toàn bộ mã nguồn kiểm tra lỗi cú pháp:
   `python -m compileall src scripts -q`

---

## 3. Xác minh an toàn (Safety Verification)
* **.gitignore:** Đã được bổ sung đầy đủ, bỏ qua các tệp môi trường `.env`, dữ liệu sinh ra trong `data/**` (ngoại trừ `.gitkeep`), cơ sở dữ liệu `database/*.duckdb` và `database/*.sqlite`, các báo cáo trong `reports/**`, bộ nhớ đệm `__pycache__/` và `.pytest_cache/`.
* **Quyền và chế độ giao dịch:** Các cấu hình `live_trading_enabled`, `real_orders_enabled`, `leverage_enabled`, và `futures_enabled` đều được đặt mặc định là `false`. Quyền tối đa trong mã nguồn là `APPROVED_FOR_DRY_RUN`. Tuyệt đối không tồn tại trạng thái `APPROVED_FOR_LIVE` trong `Permission` hoặc `StrategyStatus` (kiểm tra trong [models.py](file:///D:/AI2/QuantGit/trading-research-os/src/core/models.py)).
* **Cơ chế ngăn chặn chế độ live:** Hàm kiểm tra an toàn `assert_research_only` đã được triển khai trong [validation.py](file:///D:/AI2/QuantGit/trading-research-os/src/core/validation.py). Hàm này được gọi bắt buộc tại đầu tất cả các script chạy thông qua file khởi động chung [bootstrap.py](file:///D:/AI2/QuantGit/trading-research-os/scripts/_bootstrap.py) và tại tệp khởi động của dashboard Streamlit [streamlit_app.py](file:///D:/AI2/QuantGit/trading-research-os/src/dashboard/streamlit_app.py).

---

## 4. Xác minh luồng dữ liệu Freqtrade (Data Path Verification)
* **Chế độ explicit sample:** Cờ `--sample` trong `download_crypto_data.py` là bắt buộc để tạo dữ liệu giả lập. Nguồn dữ liệu mẫu được ghi nhận rõ ràng dưới tên `sample_freqtrade_adapter`.
* **Không tự động fallback:** Khi cờ `--use-freqtrade-cli` được bật, hệ thống sẽ thực thi trình tải dữ liệu của Freqtrade và tìm kiếm các tệp định dạng `.json`, `.json.gz`, hoặc `.feather` trong thư mục dữ liệu Freqtrade. Nếu không có CLI hoặc thiếu tệp tin, hệ thống sẽ ném lỗi rõ ràng thay vì âm thầm sinh dữ liệu mẫu giả như trước.
* **Chuẩn hóa dữ liệu:** Dữ liệu nhập từ ngoài được chuẩn hóa hoàn hảo về lược đồ đích: `symbol`, `timeframe`, `timestamp`, `open`, `high`, `low`, `close`, `volume`, `source` (với `source` được gắn nhãn là `freqtrade_cli_import`). Các kiểm tra chất lượng dữ liệu (`validate_ohlcv` trong [data_quality_checks.py](file:///D:/AI2/QuantGit/trading-research-os/src/data_brain/data_quality_checks.py)) được áp dụng đầy đủ.

---

## 5. Xác minh luồng backtest Freqtrade CLI (Backtest Verification)
* **Kết quả CLI thực tế:** Hàm `_run_freqtrade_cli` trong [batch_backtest_runner.py](file:///D:/AI2/QuantGit/trading-research-os/src/freqtrade_brain/batch_backtest_runner.py) chạy lệnh `freqtrade backtesting` với đầy đủ tham số `--userdir`, `--config`, `--strategy`, và chỉ định tệp xuất `--export-filename`.
* **Không sinh số liệu giả khi lỗi:** Nếu tiến trình Freqtrade CLI bị lỗi (mã thoát khác 0), hệ thống sẽ ghi nhận trạng thái thất bại `failed_freqtrade_cli` vào bảng `backtest_runs` cùng nội dung lỗi chi tiết và ném ngoại lệ nếu chạy ở chế độ nghiêm ngặt (`strict`). Trái lại, khi CLI thành công, kết quả xuất ra được phân tích thực tế thay vì điền số liệu rỗng.
* **Các chiến thuật spot-only:** Các chiến thuật sinh ra luôn khai báo thuộc tính `can_short = False` và nạp đè phương thức `leverage` trả về giá trị cố định `1.0`.

---

## 6. Xác minh bộ phân tích kết quả Freqtrade (Parser Verification)
* **Đầy đủ chỉ số:** Bộ phân tích [freqtrade_result_parser.py](file:///D:/AI2/QuantGit/trading-research-os/src/freqtrade_brain/freqtrade_result_parser.py) trích xuất chính xác các trường số liệu hiệu năng chính, hỗ trợ bí danh (aliases) phong phú của Freqtrade và xác định cặp giao dịch tốt nhất/tệ nhất (`best_pair` / `worst_pair`).
* **Quản lý lỗi và cảnh báo:** Nếu thiếu các trường chỉ số sau hiệu chỉnh (adjusted returns), bộ phân tích sẽ tự động sao chép chỉ số thô (total return) làm dự phòng và phát ra các cảnh báo dạng `parser_warnings` hiển thị trên Streamlit dashboard mà không làm sập ứng dụng.
* **Kiểm thử parser:** Bộ kiểm thử đơn vị bao gồm hai test case sử dụng mock JSON dữ liệu đầy đủ và thiếu trường để kiểm tra cảnh báo hoạt động ổn định.

---

## 7. Xác minh công cụ quyết định (Decision Engine Verification)
* **Không hardcode BTC/USDT:** Danh sách cặp tiền được xác định linh hoạt dựa trên dữ liệu hiệu quả cấp cặp tiền (`pair_level_metrics`), tệp đặc tả spec, hoặc dữ liệu thị trường thực tế.
* **Đưa ra quyết định theo từng symbol:** Bản ghi quyết định được lưu trữ riêng lẻ cho từng cặp tiền của chiến thuật đó (vòng lặp `for symbol in symbols` trong `build_decisions`).
* **Lưu trữ lịch sử:** Không có câu lệnh `DELETE FROM decisions` trong suốt quá trình chấm điểm. Toàn bộ lịch sử các lượt chạy được bảo toàn.
* **Ảnh hưởng của Market Regime:** Trạng thái thị trường được đối chiếu với danh sách regime phù hợp trong YAML spec. Nếu xảy ra mismatch hoặc regime không xác định, chỉ số regime sẽ bị đánh điểm thấp (40/100) làm suy giảm tổng điểm của chiến thuật một cách hợp lý.

---

## 8. Xác minh cổng rủi ro (Risk Gate Verification)
* **Divergence check:** Hỗ trợ so sánh hiệu suất backtest thô và dry-run. Nếu độ lệch vượt quá ngưỡng cấu hình `material_dry_run_divergence` (mặc định 25%), chiến thuật bị gắn cờ cảnh báo và từ chối.
* **Kiểm tra Look-ahead:** Hàm `_lookahead_review` quét qua mã nguồn YAML spec và tệp Python được sinh ra để phát hiện các từ khóa tương lai bị cấm như `shift(-`, `future_close`, `tomorrow`, v.v. Nếu phát hiện rủi ro, chiến thuật sẽ bị từ chối ngay lập tức.
* **Quy trình Archive & Promotion:**
  * Trạng thái `archived` được kiểm tra và trả về ngay rủi ro từ chối với lý do lưu trữ.
  * Việc thăng cấp lên `approved_for_dry_run` yêu cầu chiến thuật đạt đủ số lượng giao dịch tối thiểu (2 lần ngưỡng mặc định, tức là ít nhất 100 giao dịch), có lợi nhuận OOS dương, max drawdown dưới giới hạn cấu hình, và lợi nhuận sau phí lớn hơn 0.
  * Nếu không đủ giao dịch nhưng vượt qua các cổng rủi ro khác, chiến thuật được xếp vào nhóm `watchlist` hoặc `paper_only`.

---

## 9. Xác minh thẩm định đặc tả chiến thuật (Strategy Spec Validation)
* **Ràng buộc số liệu:** [strategy_spec_validator.py](file:///D:/AI2/QuantGit/trading-research-os/src/ai_strategy_brain/strategy_spec_validator.py) kiểm soát nghiêm ngặt các tham số:
  * `stop_loss` phải âm và nằm trong khoảng `(-0.50, 0.0)`.
  * `take_profit` phải dương và `<= 1.0`.
  * `max_open_trades` phải là số nguyên dương.
  * `max_pair_exposure` phải nằm trong khoảng `(0.0, 1.0]`.
  * `leverage_allowed` và `futures_allowed` bắt buộc phải là `False`.
* **Cú pháp logic:** Thẩm định sâu cấu trúc logic điều kiện vào/ra lệnh, giới hạn danh sách chỉ báo được phép (whitelist indicators). Các lỗi được gom lại thành một danh sách thông báo rõ ràng, dễ đọc.

---

## 10. Xác minh vị trí các tệp runtime sinh ra (Generated Artifacts Location)
* ** data/generated/...:** Toàn bộ đặc tả YAML mới tạo được lưu tại `data/generated/specs/`. Toàn bộ mã nguồn chiến thuật Python được chuyển đổi được lưu tại `data/generated/freqtrade_strategies/`. Không có bất kỳ tệp runtime nào bị ghi vào thư mục nguồn `src` như ở đợt đánh giá trước.
* **Khả năng liên kết:** Bản ghi chuyển đổi trong bảng `generated_strategies` chứa đường dẫn đầy đủ của tệp code sinh ra, giúp công cụ chạy backtest có thể dễ dàng định vị mã nguồn chiến thuật.

---

## 11. Xác minh bảng điều khiển (Dashboard Verification)
* **Hiển thị đầy đủ thông tin:** Dashboard Streamlit hiển thị rõ ràng nguồn dữ liệu thị trường (`market_data` nguồn sample vs CLI import), nguồn gốc chạy backtest (`engine` của backtest_runs), cảnh báo phân tích kết quả (`parser_warnings`), trạng thái rủi ro, và lý do từ chối chiến thuật.
* **Cảnh báo thiếu engine rõ ràng:** Bảng "Engine Status" chẩn đoán rõ các engine tùy chọn (LEAN, Qlib, Nautilus, OpenBB) có trạng thái "installed" hay "missing" và vai trò tương ứng của chúng.
* **An toàn:** Bảng điều khiển không chứa bất kỳ nút bấm kích hoạt tiến trình bot giao dịch thực tế hay nhập API key/secrets.

---

## 12. Xác minh kiểm thử (Test Verification)
* **Số lượng test:** 19/19 bài kiểm thử thành công.
* **Độ bao phủ:** Bộ kiểm thử bao gồm các bài kiểm thử chất lượng dữ liệu, kiểm tra parser với fixture thực tế, kiểm tra hành vi data adapter khi chạy CLI thiếu file, kiểm tra cổng rủi ro với look-ahead/dry-run divergence, kiểm tra thăng cấp chiến thuật, và đặc biệt là kiểm thử tích hợp toàn bộ pipeline (`test_full_v1_fallback_pipeline_uses_temp_paths`) chạy trên SQLite database ảo hóa độc lập.

---

## 13. Xác minh tài liệu (Documentation Verification)
* **README.md:** Đã cập nhật chi tiết. Nêu rõ trạng thái của từng engine (Freqtrade hoạt động thực tế, các engine khác ở dạng scaffold). Giải thích rõ ràng các giới hạn của chế độ dữ liệu mẫu synthetic, cơ chế chạy fallback nội bộ, và hướng dẫn khắc phục sự cố (Troubleshooting) khi thiếu Freqtrade CLI hoặc DuckDB.

---

## 14. Các rủi ro còn lại (Remaining Risks)
1. **Look-ahead kiểm tra tĩnh:** Việc lọc look-ahead dựa trên từ khóa chuỗi con có thể bị lách qua nếu chiến thuật sử dụng các thủ thuật toán học phức tạp hoặc làm mờ mã (code obfuscation). Khuyến nghị nâng cấp lên bộ phân tích AST Python ở các đợt phát triển tiếp theo.
2. **DuckDB tùy chọn:** Mặc định hệ thống tự động sử dụng SQLite nếu thiếu DuckDB. SQLite hoạt động tốt cho luồng v1 nhưng sẽ có hạn chế về hiệu năng phân tích factor lớn ở v3. Tuy nhiên điều này đã được ghi tài liệu rõ ràng.
