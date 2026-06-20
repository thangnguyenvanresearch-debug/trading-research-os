# Báo cáo audit Local AI Mode

## Scope

Audit tập trung vào Local AI Mode:

- `configs/local_ai.yaml`
- `database/schema.sql`
- `src/ai/local_ai_client.py`
- `src/ai/research_engine.py`
- `scripts/run_local_ai_research.py`
- `src/dashboard/pages/12_local_ai_research.py`
- `tests/test_local_ai_client.py`
- `tests/test_research_engine.py`
- `README.md`

Không sửa source code. Chỉ tạo file audit trong `audit_local_ai_mode`.

## Commands run

- `python -m compileall src scripts -q`: passed
- `python -m compileall src/dashboard -q`: passed
- `python -m pytest -q`: passed, `58 passed in 4.68s`
- Ollama check bằng here-string Python: passed command, result `ollama_unavailable: URLError`
- `python scripts/run_local_ai_research.py --symbols AAPL MSFT --provider yfinance --interval 1d --task-type market_review`: passed graceful-unavailable path
- Safe workflow:
  - `python scripts/init_database.py`: passed
  - `python scripts/download_crypto_data.py --sample --pairs BTC/USDT ETH/USDT --timeframe 1h`: passed
  - `python scripts/build_features.py`: passed, `1856 feature rows`
  - `python scripts/generate_strategy_specs.py --asset-class crypto --count 3`: passed
  - `python scripts/convert_specs_to_freqtrade.py`: passed
  - `python scripts/run_freqtrade_backtests.py`: passed
  - `python scripts/score_strategies.py --latest-only`: passed

Một command check Ollama inline đầu tiên fail do quoting PowerShell/SyntaxError, sau đó được chạy lại bằng here-string và pass. Đây là lỗi invocation, không phải lỗi project.

## 1. Safety and forbidden integration audit

Kết quả: **implemented / safe**

Safety grep trên `configs/src/scripts/tests/README.md` tìm thấy các pattern nhạy cảm nhưng đều là:

- cấu hình phủ định: `configs/local_ai.yaml` có `allow_chatgpt_oauth: false`;
- test phủ định: các test assert không có OpenAI/ChatGPT/order function;
- README giải thích không dùng OpenAI API/ChatGPT OAuth/cookie;
- `src/data_brain/openbb_adapter.py` có regex redaction cho secret-like text, không phải secret thật.

Không phát hiện:

- OpenAI API integration;
- ChatGPT OAuth/login;
- cookie/session storage;
- browser automation login;
- password handling;
- order placement;
- live trading/futures/leverage enablement;
- runtime `APPROVED_FOR_LIVE`.

## 2. Local AI config audit

File: `configs/local_ai.yaml`

Kết quả: **implemented**

Config đúng yêu cầu:

- `provider: ollama`
- `base_url: http://localhost:11434`
- `model: llama3.1:8b`
- `timeout_seconds: 120`
- `max_context_chars: 24000`
- `temperature: 0.2`
- `safe_mode: true`
- `allow_external_api: false`
- `allow_openai_api: false`
- `allow_chatgpt_oauth: false`
- `allow_browser_automation: false`
- task list được kiểm soát.

Nhận xét: `allow_external_api: false` chưa được enforce trực tiếp; enforcement hiện dựa vào `safe_mode=true`.

## 3. Database schema audit

File: `database/schema.sql`

Kết quả: **implemented**

Bảng `ai_research_memos` tồn tại với các field:

- `memo_id`
- `created_at`
- `provider`
- `model`
- `task_type`
- `symbols`
- `source_context_json`
- `prompt_text`
- `response_text`
- `status`
- `warnings_json`
- `metadata_json`

`python scripts/init_database.py` chạy pass và tạo/giữ schema. Môi trường base fallback SQLite do DuckDB unavailable; SQLite path hoạt động.

DuckDB compatibility: **likely**, vì schema dùng kiểu TEXT/REAL/INTEGER cơ bản và pattern đã dùng chung với các bảng hiện có. Không xác minh DuckDB runtime vì DuckDB không available trong env base.

## 4. Local AI client audit

File: `src/ai/local_ai_client.py`

Kết quả: **implemented**

Xác minh:

- `get_local_ai_status()` gọi `/api/version`, timeout tối đa 5 giây cho health check.
- `generate_with_local_ai()` POST tới `/api/generate`.
- Payload có `stream: False`, `model`, `prompt`, `temperature`.
- Không dùng API key.
- Không import OpenAI client.
- Không gọi ChatGPT.
- Non-localhost base URL bị reject khi `safe_mode=true`.
- Error trả về dict structured, không crash.

Không phát hiện execution/order surface.

## 5. Research engine audit

File: `src/ai/research_engine.py`

Kết quả: **implemented**

Xác minh:

- `build_research_context()` đọc local DB qua analytics helpers và `fetch_dataframe`.
- Có OpenBB summary, data quality, correlation matrix.
- Có optional backtests/risk reviews/decisions.
- Empty DB được xử lý bằng warning, không crash.
- Context markdown được truncate theo `max_context_chars`.
- Prompt có yêu cầu:
  - analyze only provided local data;
  - distinguish facts/assumptions/missing data;
  - do not give direct buy/sell orders;
  - do not treat backtests as proof of future profit;
  - explain data quality problems;
  - research analysis, not trading advice.
- `run_local_ai_research()` lưu DB và markdown report.
- Khi Ollama unavailable, lưu status `failed`, warning/error rõ ràng.

Low issue: `_safe_fetch()` bắt toàn bộ exception và trả DataFrame rỗng, có thể che lỗi query/schema trong một số trường hợp.

## 6. CLI audit

File: `scripts/run_local_ai_research.py`

Kết quả: **implemented**

Xác minh:

- Import `_bootstrap.py`, gián tiếp gọi `assert_research_only`.
- Hỗ trợ:
  - `--symbols`
  - `--provider`
  - `--interval`
  - `--task-type`
  - `--include-backtests`
  - `--include-risk`
  - `--include-decisions`
  - `--model`
  - `--base-url`
- Không yêu cầu OpenAI API.
- Không yêu cầu internet/cloud.
- Không gọi ChatGPT.
- In `memo_id`, `status`, `provider`, `model`, `output_path`, warnings/errors.

Runtime:

- Ollama unavailable.
- CLI exit code 0.
- Memo failed được lưu: `memo_de999fc87977`.

## 7. Dashboard audit

File: `src/dashboard/pages/12_local_ai_research.py`

Kết quả: **implemented**

Xác minh:

- Hiển thị local AI status.
- Hiển thị latest AI memos.
- Có form chọn symbols/provider/interval/task/include flags.
- Button `Run local AI research` gọi local research engine.
- Không có OpenAI API key input.
- Không có ChatGPT OAuth.
- Không có cookie/session/browser automation.
- Không có buy/sell/order controls.
- Có warning: local AI research, not trading advice, does not place orders.

Low usability note: page load gọi local status endpoint; an toàn nhưng có thể chờ timeout khi Ollama không chạy.

## 8. Tests audit

Kết quả: **implemented**

`python -m pytest -q`: `58 passed`.

Tests cover:

- local AI unavailable;
- non-localhost base URL rejected in safe mode;
- mocked Ollama response;
- prompt includes no-buy/sell and backtest caution;
- empty DB context;
- mocked OpenBB rows;
- unavailable handling inserts failed memo;
- mocked completed memo insert;
- no OpenAI/ChatGPT backend strings in implementation;
- no order surface in client.

Tests không yêu cầu Ollama chạy và không yêu cầu internet.

## 9. Compile audit

Kết quả: **implemented**

- `python -m compileall src scripts -q`: passed
- `python -m compileall src/dashboard -q`: passed

## 10. Optional Ollama smoke test

Kết quả: **not verifiable / unavailable**

Ollama endpoint `http://localhost:11434/api/version` trả `URLError`.

Không cài Ollama tự động. Không tạo real local model memo. Chỉ xác minh được unavailable path.

## 11. Regression audit

Kết quả: **no regression detected**

Safe Freqtrade/sample workflow pass end-to-end. Local AI Mode không phá:

- sample crypto data import;
- feature build;
- strategy spec generation;
- Freqtrade strategy conversion;
- fallback backtest;
- risk/decision scoring.

## Remaining risks

Không có blocker. Các điểm còn lại là low-priority:

- enforce `allow_external_api` độc lập với `safe_mode`;
- tránh broad exception swallowing trong `_safe_fetch()`;
- cân nhắc cache local AI status trên dashboard để giảm delay khi Ollama unavailable.
