# Qlib Integration Scorecard

| Hạng mục | Điểm / 10 | Nhận xét |
|---|---:|---|
| Safety invariants | 9.5 | Không phát hiện cloud/live/order/credential enablement. |
| Config safety | 9.5 | Qlib optional, research-only, daily disabled by default. |
| Schema | 9.0 | Tables đúng yêu cầu, init DB pass. |
| Adapter unavailable behavior | 9.5 | Missing Qlib handled cleanly, no install/fetch. |
| Local data bridge | 9.0 | Reads local OpenBB, dedupe/sort/export OK. |
| No-lookahead features | 9.0 | Features trailing/current only; future return separated as label. |
| Runner unavailable path | 9.0 | Saves run/report, no fake metrics/predictions. |
| True Qlib execution | 5.5 | Not verified because Qlib not installed; future branch still baseline-only. |
| CLI usability | 9.0 | Required args supported, smoke tests pass. |
| Dashboard page | 8.0 | Source/compile OK; visual not verified because Streamlit not running. |
| Tests | 9.0 | `120 passed`; good coverage for missing/unavailable and dataset export. |
| Overall readiness | 8.8 | Safe partial integration, ready to checkpoint. |

## Overall

**8.8 / 10**
