# Scorecard Round 3

| Hạng mục | Điểm /10 | Nhận xét |
|---|---:|---|
| Safety invariants | 9.8 | Không thấy live/futures/leverage/real orders/API key path. `APPROVED_FOR_LIVE` chỉ xuất hiện trong README như tuyên bố không tồn tại. |
| AST look-ahead detection | 9.0 | AST analyzer tồn tại, dùng `ast`, phát hiện negative shift, future iloc, future identifiers, parse error strict-safe. Còn là static heuristic, chưa data-flow sâu. |
| Risk gate integration | 8.8 | Risk gate gọi substring + AST analyzer, thu inspected paths; reject look-ahead risk. Minor: inspected paths chưa được persist vào flags. |
| SQLite fallback warning | 9.3 | Warning rõ ràng, một lần/process, test monkeypatch DuckDB unavailable. |
| Optional engine diagnostics | 8.8 | Status object chuẩn, `safe_for_live: false`, dashboard dùng. FinceptTerminal chưa có adapter riêng, nhưng không bị trình bày sai. |
| Dashboard honesty | 9.0 | Hiển thị status/capability/next step/safe_for_live; không thấy live controls hoặc bot launch. |
| Documentation accuracy | 9.2 | README mô tả Round 3, scaffold engines, fallback/sample limitations, safety defaults. |
| Test coverage | 8.8 | 27 tests pass; cover AST, fallback warning, optional engines, full fallback. Thiếu pytest case riêng cho keyword `shift(periods=-1)`. |
| Code quality | 8.7 | Thay đổi gọn, không redesign; AST analyzer đọc được. Còn heuristic và một vài taxonomy inconsistencies. |
| Regression safety | 9.2 | Compile, pytest, safe workflow đều pass; không phát hiện regression. |
| Retail-user practicality | 8.8 | Người dùng dễ biết SQLite fallback, engine scaffold, sample/fallback status. Vẫn là research OS, chưa production multi-engine. |
| Overall project readiness | 9.1 | V1 local research/demo path an toàn và minh bạch; các phase production engine còn là kế hoạch. |

