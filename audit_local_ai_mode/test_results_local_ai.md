# Test Results Local AI

## Compile

```powershell
python -m compileall src scripts -q
```

Result: passed.

```powershell
python -m compileall src/dashboard -q
```

Result: passed.

## Pytest

```powershell
python -m pytest -q
```

Result:

```text
58 passed in 4.68s
```

## Ollama availability

First inline command failed due to PowerShell quoting/SyntaxError. Re-run with here-string:

```powershell
@'
import urllib.request
try:
    print(urllib.request.urlopen('http://localhost:11434/api/version', timeout=5).read().decode())
except Exception as e:
    print('ollama_unavailable:', type(e).__name__)
'@ | python -
```

Result:

```text
ollama_unavailable: URLError
```

## Local AI CLI

```powershell
python scripts/run_local_ai_research.py --symbols AAPL MSFT --provider yfinance --interval 1d --task-type market_review
```

Result: passed graceful-unavailable path.

Summary:

- `memo_id=memo_de999fc87977`
- `status=failed`
- `provider=ollama`
- `model=llama3.1:8b`
- output path: `reports/local_ai/memo_de999fc87977_market_review.md`
- error/warning: local Ollama connection refused

## ai_research_memos DB check

Query after audit:

```text
memos = 2
latest: memo_de999fc87977, status failed, provider ollama, model llama3.1:8b, task market_review
```

## Safe workflow regression

Commands:

```powershell
python scripts/init_database.py
python scripts/download_crypto_data.py --sample --pairs BTC/USDT ETH/USDT --timeframe 1h
python scripts/build_features.py
python scripts/generate_strategy_specs.py --asset-class crypto --count 3
python scripts/convert_specs_to_freqtrade.py
python scripts/run_freqtrade_backtests.py
python scripts/score_strategies.py --latest-only
```

Results:

- init database: passed
- sample data: passed, BTC/USDT and ETH/USDT 720 candles each
- feature build: passed, `1856 feature rows`
- generate specs: passed, 3 specs
- convert specs: passed, 3 Freqtrade strategy files
- fallback backtests: passed
- score strategies: passed, 3 latest decisions printed, all rejected by risk gate

## Notes

Base environment emitted expected DuckDB-to-SQLite fallback warnings. This is not a Local AI failure.
