# Audit LEAN CLI Compatibility Patch - Full Report

## Scope

Audit chỉ tập trung vào patch tương thích LEAN CLI sau audit trước:

- `src/lean_brain/lean_adapter.py`
- `src/lean_brain/lean_runner.py`
- `src/lean_brain/lean_project_builder.py`
- `tests/test_lean_adapter.py`
- `tests/test_lean_runner.py`
- generated project: `data/generated/lean/projects/equal_weight_demo_lean_5a615f2a482e`

Không chạy lại executable LEAN backtest dài. Chỉ chạy compile, pytest, skip-run, DB verification và safety grep.

## Commands Run

- `.\.venv-openbb\Scripts\python.exe -m compileall src scripts -q` - passed
- `.\.venv-openbb\Scripts\python.exe -m compileall src\dashboard -q` - passed
- `.\.venv-openbb\Scripts\python.exe -m pytest -q` - passed, `104 passed`
- `.\.venv-openbb\Scripts\lean.exe --version` - passed, `lean 1.0.225`
- `docker info --format '{{json .ServerVersion}}'` - failed, Docker daemon unavailable
- `.\.venv-openbb\Scripts\python.exe scripts\run_lean_backtest.py --symbols AAPL MSFT --provider yfinance --interval 1d --strategy-name equal_weight_demo --skip-run` - passed
- DB verification for `lean_backtest_runs` and `lean_backtest_metrics` - passed
- HTTP dashboard check `http://localhost:8501` - failed, Streamlit not running
- Safety grep over `configs src scripts tests README.md` - no unsafe enablement found

## Safety Audit

Status: **implemented / safe**

Không phát hiện runtime dùng:

- `lean login`
- QuantConnect cloud login
- brokerage credentials
- API keys/passwords/tokens
- live trading mode
- futures/leverage enablement
- real order placement
- OpenAI API / ChatGPT OAuth / cookie automation

Các hit từ safety grep là false-positive/expected:

- README và tests có các negative assertions như không có `APPROVED_FOR_LIVE`.
- `configs/lean.yaml` đặt các flag unsafe là `false`.
- `src/ai/local_ai_client.py` có blocklist OpenAI/ChatGPT endpoint.
- `src/lean_brain/lean_project_builder.py` có `SetHoldings` trong generated LEAN skeleton local backtest. Đây là mô phỏng LEAN backtest, không phải order thực/brokerage/live.

## Patch Audit: LEAN CLI Discovery

File: `src/lean_brain/lean_adapter.py`

Status: **implemented**

Evidence:

- `_lean_cli_path()` ưu tiên `shutil.which("lean")`.
- Nếu không có global PATH, fallback tới:
  - `PROJECT_ROOT / ".venv-openbb" / "Scripts" / "lean.exe"`
- `get_lean_status()` trả về `lean_cli_path`.
- `safe_for_live` luôn là `False`.
- `assert_lean_research_only()` vẫn reject:
  - live trading
  - brokerage credentials
  - QuantConnect cloud
  - real orders
  - futures
  - leverage

Finding thấp:

- `docker_available` hiện chỉ kiểm tra `shutil.which("docker")`, nên báo Docker CLI tồn tại nhưng không xác minh daemon. Trong audit này `get_lean_status()` báo docker available, còn `docker info` fail. Nên đổi nhãn thành `docker_cli_available` hoặc thêm daemon check ở pass sau.

## Patch Audit: Runner Command

File: `src/lean_brain/lean_runner.py`

Status: **implemented**

Evidence:

- Runner dùng `status.get("lean_cli_path") or "lean"`.
- Command gồm:
  - `backtest`
  - project path
  - `--lean-config`
  - generated `lean.json`
- Timeout được giới hạn `900` giây.
- Exception được ghi vào `errors_json`, report markdown và DB run record.
- Metrics chỉ được record nếu `parse_lean_results()` có metrics thật.
- `lean_backtest_metrics` hiện empty, đúng vì chưa có result/statistics JSON thật.

## Patch Audit: Generated lean.json/config.json

Files:

- `src/lean_brain/lean_project_builder.py`
- `data/generated/lean/projects/equal_weight_demo_lean_5a615f2a482e/lean.json`
- `data/generated/lean/projects/equal_weight_demo_lean_5a615f2a482e/config.json`
- `data/generated/lean/projects/equal_weight_demo_lean_5a615f2a482e/Main.py`
- `data/generated/lean/projects/equal_weight_demo_lean_5a615f2a482e/README.md`

Status: **implemented / safe**

Evidence:

- `lean.json` có `live-mode: false`.
- `organization-id` và `job-organization-id` là placeholder toàn số 0, không phải credential.
- Không có username/password/token/API key.
- Không có brokerage config.
- README ghi rõ:
  - No live trading.
  - No brokerage credentials.
  - No QuantConnect cloud login.
  - No futures.
  - No leverage.
  - No real orders.
- `Main.py` ghi rõ research-only local backtesting.

Ghi chú:

- `api-handler: QuantConnect.Api.Api` là handler class trong config LEAN, không đi kèm credential hoặc login. Không xác minh được liệu LEAN runtime có cố gọi cloud không khi không có credential, vì executable run timeout.

## Test Audit

Status: **passed**

`104 passed`.

Tests cover:

- venv-local LEAN CLI discovery.
- no-LEAN-installed scenario bằng temp project root.
- unsafe LEAN config rejection.
- generated project includes `config.json` and `lean.json`.
- generated `lean.json` has `live-mode: false`.
- runner command contains `--lean-config`.
- parser does not invent metrics.
- dashboard page compiles.

## Runtime Smoke Without Long LEAN Execution

Command:

`.\.venv-openbb\Scripts\python.exe scripts\run_lean_backtest.py --symbols AAPL MSFT --provider yfinance --interval 1d --strategy-name equal_weight_demo --skip-run`

Result:

- run_id: `lean_bt_3f8ecb692783`
- status: `skeleton_created`
- project_path: `D:\AI2\QuantGit\trading-research-os\data\generated\lean\projects\equal_weight_demo_lean_ca37bf610253`
- report_path: `D:\AI2\QuantGit\trading-research-os\reports\lean\lean_bt_3f8ecb692783_equal_weight_demo.md`
- warning: LEAN run skipped by request
- errors: `[]`

Data export:

- AAPL: 1115 rows
- MSFT: 1115 rows

## DB Verification

Latest records:

- `lean_bt_3f8ecb692783`: `skeleton_created`
- `lean_bt_f4d0947fa6ef`: `failed`, timeout after 900 seconds
- `lean_bt_588e60d6e28d`: `failed`, missing lean config before patch

Metrics:

- `lean_backtest_metrics` empty.
- Không phát hiện fake metrics.

## Dashboard Check

HTTP check failed:

- `URLError [WinError 10061]`

Interpretation:

- Streamlit không chạy tại `localhost:8501`.
- Đây không phải lỗi source của patch.
- Page `14_lean_backtests` nên hiển thị latest LEAN runs khi dashboard được start.
- Visual inspection: **not verified**.

## Verdict

**accepted_with_minor_followups**

Patch hiện tại an toàn để checkpoint. Executable LEAN backtest vẫn chưa verified và nên được tách sang phase Docker/LEAN runtime diagnostics riêng, không nên trộn vào Qlib phase.
