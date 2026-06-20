# LEAN CLI Compatibility Patch Scorecard

| Hạng mục | Điểm / 10 | Nhận xét |
|---|---:|---|
| Safety invariants | 9.5 | Không phát hiện cloud login, credentials, brokerage, live/futures/leverage/real orders. |
| LEAN CLI discovery | 9.0 | Detect được `.venv-openbb\Scripts\lean.exe`; không cần global PATH. |
| Runner command safety | 9.0 | Dùng explicit `--lean-config`, timeout bounded, report/DB lưu lỗi. |
| Local lean.json/config.json | 8.5 | Local-only, no credentials, `live-mode=false`; vẫn chưa xác minh runtime hoàn chỉnh. |
| Metrics integrity | 10.0 | Không invent metrics; metrics table empty khi run fail. |
| Test coverage | 9.0 | `104 passed`; có tests cho venv CLI, safe config, `--lean-config`. |
| Runtime verification | 5.5 | skip-run pass; executable run timeout nên chưa verified. |
| Docker diagnostics | 6.5 | Docker daemon fail được ghi nhận; status helper còn lẫn CLI vs daemon. |
| Dashboard readiness | 7.0 | Page compile/source OK, nhưng HTTP failed vì Streamlit không chạy. |
| Documentation/reporting | 8.5 | Reports và DB lưu trạng thái rõ, không che lỗi. |
| Readiness to checkpoint | 9.0 | An toàn để checkpoint và chuyển Qlib; LEAN executable để phase riêng. |

## Overall

**8.9 / 10**
