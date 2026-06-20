# Daily Research Pipeline Details

## Commands run

### Compile and tests

```powershell
python -m compileall src scripts -q
python -m compileall src/dashboard -q
python -m pytest -q
```

Results:

- compile `src scripts`: passed
- compile `src/dashboard`: passed
- pytest: `74 passed in 4.69s`

### Dry run

```powershell
python scripts/run_daily_research.py --symbols AAPL MSFT --provider yfinance --interval 1d --task-type daily_research_note --model qwen2.5:3b --dry-run
```

Output summary:

```text
run_id=daily_ff7f9d4fa5b9
status=dry_run
symbols=AAPL,MSFT
provider=yfinance
interval=1d
analytics_report_path=D:\AI2\QuantGit\trading-research-os\reports\daily_research\daily_ff7f9d4fa5b9\daily_research_summary.md
local_ai_memo_id=None
local_ai_report_path=None
warnings=Dry run only: no OpenBB ingestion or Local AI call executed.
```

### Ollama checks

```powershell
python - << service check via here-string
```

Result:

```json
{"version":"0.30.8"}
```

Model tags:

```json
{"name":"qwen2.5:3b","model":"qwen2.5:3b","parameter_size":"3.1B","quantization_level":"Q4_K_M"}
```

### Real run

```powershell
python scripts/run_daily_research.py --symbols AAPL MSFT --provider yfinance --interval 1d --task-type daily_research_note --model qwen2.5:3b
```

Output summary:

```text
run_id=daily_f3e6beb62b78
status=completed_with_warnings
symbols=AAPL,MSFT
provider=yfinance
interval=1d
analytics_report_path=D:\AI2\QuantGit\trading-research-os\reports\daily_research\daily_f3e6beb62b78\daily_research_summary.md
local_ai_memo_id=memo_15a2221eb8b2
local_ai_report_path=D:\AI2\QuantGit\trading-research-os\reports\local_ai\memo_15a2221eb8b2_daily_research_note.md
warnings=OpenBB is not installed. Install optional OpenBB support or keep using the Freqtrade/sample workflow.; OpenBB ingestion status: missing_openbb; Context markdown truncated to 24000 characters.
```

## DB verification

Latest daily run:

```text
run_id=daily_f3e6beb62b78
status=completed_with_warnings
local_ai_memo_id=memo_15a2221eb8b2
```

Latest Local AI memo:

```text
memo_id=memo_15a2221eb8b2
status=completed
task_type=daily_research_note
response_len=2183
```

## Report file verification

Daily research report folder:

```text
reports/daily_research/daily_f3e6beb62b78/
  daily_research_summary.json
  daily_research_summary.md
  openbb_summary.csv
```

Local AI report:

```text
reports/local_ai/memo_15a2221eb8b2_daily_research_note.md
```

Verified content:

- daily report contains run id and research-only/no-orders notice.
- Local AI report contains memo id, response section, prompt section, and no-orders notice.

## Dashboard status

```powershell
python -m compileall src/dashboard -q
```

Result: passed.

HTTP check:

```text
http://localhost:8501 -> 200
```

Visual dashboard inspection was not automated. Manual inspection of page `13_daily_research` is recommended.

## Safety grep

Searched:

```text
OPENAI_API_KEY
api.openai.com
chatgpt.com/auth
oauth
cookie
browser automation
playwright
selenium
password
create_order
place_order
market_order
limit_order
buy_order
sell_order
live_trading_enabled: true
real_orders_enabled: true
leverage_enabled: true
futures_enabled: true
APPROVED_FOR_LIVE
approved_for_live
```

No unsafe integration or live/order enablement found.

Allowed/explained hits:

- config flags set to false;
- Local AI denylist for forbidden OpenAI/ChatGPT hosts;
- tests asserting order/live surfaces are absent;
- README explanatory text;
- OpenBB secret-redaction regex;
- scheduler helper text explicitly says it does not store passwords/cookies.

## Remaining issues

- Real run used base Python, where OpenBB package was not installed, so fresh OpenBB ingestion was skipped safely. Existing local OpenBB rows were still available for analytics and Local AI context.
- Manual dashboard visual inspection remains.
