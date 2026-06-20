# Control Center Scorecard

| Hạng mục | Điểm / 10 | Nhận xét |
|---|---:|---|
| Safety invariants | 9.5 | Không phát hiện live/order/credential/cloud enablement. |
| Read-only dashboard behavior | 9.0 | Page không có buttons chạy engine; chỉ đọc DB/config. |
| Helper read-only behavior | 8.0 | Helpers đọc DB/config; CLI gọi init DB nên không pure read-only metadata-wise. |
| Engine status accuracy | 7.0 | LEAN `ready` overstates executable readiness; Daily Scheduler label là DB run, không Task Scheduler check. |
| OpenBB data health | 9.0 | Row count/duplicate health hợp lý. |
| Qlib status | 9.0 | Missing/execution unverified được phản ánh đúng. |
| LEAN status | 6.5 | CLI detected đúng nhưng executable timeout chưa được phản ánh trong card chính. |
| Safety checklist | 8.5 | Config false flags tốt; không xác minh mọi runtime external state. |
| CLI report | 8.0 | Report pass; wording cần rõ hơn về LEAN/Daily. |
| Tests | 9.0 | `129 passed`; thêm tests cho status wording/truncation sẽ tốt hơn. |
| Dashboard visual | 7.0 | Compile pass, HTTP không verified do Streamlit không chạy. |
| Overall | 8.6 | Safe to checkpoint với minor accuracy followups. |

## Overall Score

**8.6 / 10**
