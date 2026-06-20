# Audit Control Center - Full Report

## Scope

Audit tập trung vào Multi-Engine Research Control Center:

- `src/dashboard/control_center.py`
- `src/dashboard/pages/00_research_control_center.py`
- `src/dashboard/app.py`
- `scripts/report_control_center_status.py`
- `tests/test_control_center.py`
- `README.md`

Không sửa source. Không chạy engine/backtest/LLM generation. Chỉ đọc source, chạy compile/test/CLI report, DB read-only verification, safety grep.

## Commands Run

- `python -m compileall src scripts -q` - passed
- `python -m compileall src\dashboard -q` - passed
- `python -m pytest -q` - passed, `129 passed`
- `python scripts\report_control_center_status.py` - passed
- DB verification queries - passed
- Dashboard HTTP check `localhost:8501` - failed, Streamlit not running
- Safety grep over `configs src scripts tests README.md` - no unsafe enablement found

## Safety Audit

Status: **implemented / safe**

Không phát hiện:

- OpenAI API integration.
- ChatGPT OAuth.
- cookies/session/browser automation.
- password handling.
- cloud credential integration.
- brokerage/live/order enablement.
- futures/leverage enablement.
- remote dataset fetch.
- order controls trong Control Center page.

Safety grep hits đều là expected:

- README/tests mô tả forbidden behavior hoặc safety statements.
- Configs đặt unsafe flags là `false`.
- Local AI blocklist có `api.openai.com` và `chatgpt.com`.
- `SetHoldings` chỉ nằm trong LEAN research-only skeleton.

## Helper Audit

File: `src/dashboard/control_center.py`

Status: **partially implemented**

Read-only behavior:

- Các helper đọc config và DB.
- Không gọi ingestion/backtest/experiment runner.
- Không place orders.
- Không gọi OpenAI/ChatGPT.
- Không gọi external internet. Local AI status gọi local Ollama endpoint `localhost` với timeout ngắn.
- Missing tables được xử lý bằng empty DataFrame trong `_safe_fetch_dataframe()`.

Issues:

1. `write_control_center_report()` ghi markdown report, đúng scope CLI report.
2. `scripts/report_control_center_status.py` gọi `initialize_database()`. Nếu DB chưa có schema, lệnh này có thể tạo bảng. Vì yêu cầu CLI “does not modify DB”, đây là một điểm lệch nhỏ. Nó không sửa dữ liệu research, nhưng không phải pure read-only.
3. Warning/error summaries lấy nguyên JSON text từ DB, chưa truncate. Với lỗi lớn, dashboard/report có thể ồn hoặc nặng.
4. `build_latest_runs()` gọi `get_latest_qlib_exports(limit)` hai lần; không sai nhưng dư query.

## Engine Status Accuracy Audit

### OpenBB

Status: **accurate**

DB verification:

- AAPL/yfinance/1d: 1115 rows, 1115 distinct timestamps.
- MSFT/yfinance/1d: 1115 rows, 1115 distinct timestamps.
- Total: 2230 rows.

`has_data` là hợp lý.

### Local AI

Status: **mostly accurate**

Control Center dùng `get_local_ai_status({"timeout_seconds": 2})`, tức kiểm local Ollama endpoint hiện tại, không chỉ dựa vào memo lịch sử. Nếu local endpoint chậm, page có thể đợi tối đa ngắn; không phải long-running.

### Daily Scheduler

Status: **partially accurate / wording issue**

Control Center hiển thị key `daily_scheduler`, nhưng data lấy từ `daily_research_runs` latest DB row. Nó không query Windows Task Scheduler. Vì vậy status này nên được gọi là `latest_daily_run`, không nên ngầm đảm bảo scheduled task hiện vẫn registered/active.

### LEAN

Status: **overstated**

Control Center hiển thị:

```json
"lean": {"status": "ready", "cli": true, "safe_for_live": false}
```

Nhưng audit history/DB cho thấy executable LEAN vẫn chưa verified:

- `lean_bt_f4d0947fa6ef`: failed timeout after 900 seconds.
- latest skip-run `lean_bt_3f8ecb692783`: `skeleton_created`.

Do đó `ready` dễ bị hiểu là executable-ready. Nên đổi wording thành `cli_detected_executable_unverified` hoặc hiển thị riêng:

- CLI detected: true
- skeleton/data bridge: available
- executable backtest: unverified/last failed timeout

Điểm cộng: next actions có câu “LEAN executable backtest remains future Docker/runtime diagnostics.”

### Qlib

Status: **accurate**

Qlib package missing, Control Center hiển thị `missing`. Dataset export available được ghi ở next actions.

### Safety

Status: **mostly accurate**

Checklist dựa trên config false flags. Nếu config thiếu, `_check_false()` trả `not verified`, và aggregate safety không thành safe. Với config hiện tại, `safe` là hợp lý.

## Dashboard Page Audit

File: `src/dashboard/pages/00_research_control_center.py`

Status: **implemented / safe**

Findings:

- Không có run buttons.
- Không có API key input.
- Không có credential forms.
- Không có cloud login forms.
- Không có live trading toggles.
- Không có order controls.
- Page gọi helper đọc local DB/config và local status only.
- Empty DataFrames được render bằng `dataframe_or_message()`.

Accuracy issue:

- Status card LEAN hiển thị `ready`, cần wording rõ hơn.

## App Entry Audit

File: `src/dashboard/app.py`

Status: **safe**

Wrapper chỉ import `dashboard.streamlit_app` sau khi add `src` vào path. Không tự chạy engine, scheduler, backtest, experiment hay credentials flow.

## CLI Report Audit

File: `scripts/report_control_center_status.py`

Status: **implemented with minor caveat**

Command pass:

```text
report_path=D:\AI2\QuantGit\trading-research-os\reports\control_center\control_center_status_2026-06-19T195003_0000.md
safety_unsafe_count=0
```

No engine execution detected.

Caveat:

- Calls `initialize_database()`, which can create missing schema tables. This is not data mutation, but technically not strictly DB read-only.

## README Audit

Status: **implemented**

README documents:

- Control Center is read-only.
- no external ingestion on page load.
- no LLM recommendations.
- no credentials/cloud login/API key forms/orders.

Missing/weak:

- Does not explicitly repeat that LEAN executable remains unverified and Qlib true trainer remains future work inside Control Center section. Those caveats exist elsewhere, but this section could be more explicit.

## Test Audit

Status: **passed**

`129 passed`.

Tests cover:

- missing tables.
- registry load.
- safety checklist items.
- next actions for Qlib missing and Local AI unavailable.
- dashboard page compile.
- CLI report writes markdown.
- no live/order surface in helper.

Coverage gap:

- No test currently asserts LEAN status wording does not overstate executable readiness.
- No test asserts warning/error summary truncation.

## DB Verification

Latest records confirm:

- Daily runs exist; latest status `completed_with_warnings`.
- Local AI latest memo completed with response length 1947.
- LEAN latest run is skip-run `skeleton_created`; earlier executable run failed timeout.
- Qlib latest run is `unavailable`.
- OpenBB AAPL/MSFT rows are deduped: rows equal distinct timestamps.

## Dashboard HTTP

Result:

```text
URLError: [WinError 10061] connection refused
```

Streamlit was not running. Not a source failure.

## Verdict

**accepted_with_minor_followups**

Control Center is safe to checkpoint. It is read-only enough for practical use, but status wording should be tightened before presenting it to non-technical users.
