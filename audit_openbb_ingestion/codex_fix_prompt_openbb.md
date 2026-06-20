# Codex Fix Prompt OpenBB

Use this as a focused follow-up prompt only if you want to harden the OpenBB ingestion layer. Do not enable live trading, futures, leverage, real orders, API key forms, or real exchange configs.

```
You are Codex working in D:\AI2\QuantGit\trading-research-os.

TASK MODE: Focused OpenBB ingestion hardening.

Do not rewrite the architecture. Keep OpenBB as research/data ingestion only.

Verified low-priority audit findings to fix:

1. Harden `src/feature_brain/openbb_feature_bridge.py` against missing OpenBB tables.
   - If `openbb_market_data` does not exist or DB is not initialized, return an empty DataFrame with the expected feature input columns.
   - Do not hide unrelated errors silently; log or return a clear empty result only for missing-table cases.
   - Add a test using a temp DB or monkeypatch to confirm missing table does not crash.

2. Improve malformed OpenBB market data handling in `src/data_brain/openbb_adapter.py`.
   - If no timestamp/date/datetime/time/index column exists in provider output, add a warning and skip that symbol instead of storing positional RangeIndex timestamps.
   - Add a test for malformed provider output without timestamp.

3. Optional maintainability cleanup only if small:
   - Split normalization helpers from `openbb_adapter.py` into a small module such as `openbb_normalizer.py`.
   - Do not change public behavior.

Run only safe checks:

python -m compileall src scripts -q
python -m pytest -q

Do not run external OpenBB fetches unless OpenBB is installed and the provider is no-key. Do not add credentials.
```
