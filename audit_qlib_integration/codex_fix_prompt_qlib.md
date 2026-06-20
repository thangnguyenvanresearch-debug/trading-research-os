# Follow-up Prompt - Optional Qlib Hardening

This is optional future work, not urgent remediation.

You are Codex working in:

`D:\AI2\QuantGit\trading-research-os`

TASK MODE:
Focused Qlib hardening only.

Do not enable live trading.
Do not enable futures.
Do not enable leverage.
Do not place real orders.
Do not add brokerage configs.
Do not add cloud credentials.
Do not fetch remote Qlib datasets.
Do not use OpenAI API or ChatGPT OAuth.

Current verified state:

- Qlib integration audit accepted with minor followups.
- Qlib is not installed.
- Dataset export works from local OpenBB data.
- Latest dataset has 2220 rows, 13 columns, no duplicate symbol+timestamp.
- Features use trailing/current data; `label_forward_return_5d` is separated as label.
- Normal run status is `unavailable` when Qlib is missing.
- Metrics/predictions count is 0 when Qlib is unavailable.
- Tests pass: 120 passed.

Optional improvements:

1. Add stricter feature formula tests:
   - `close_return_5d`
   - `momentum_20d`
   - `volatility_20d`
   - `volume_zscore_20d`
   - verify label is excluded from manifest `feature_columns`

2. Improve future Qlib-installed branch:
   - do not store pandas baseline outputs in `qlib_predictions`, or
   - store them in a clearly separate baseline section/table/report field.
   - reserve `qlib_predictions` for true Qlib model output.

3. Add dashboard empty-table resilience tests for page 15 if practical.

4. Later, in a separate phase, install Qlib and implement a true local-only Qlib trainer:
   - use exported local dataset only
   - no remote dataset
   - no cloud credentials
   - no live trading
   - no orders

Run:

```powershell
python -m compileall src scripts -q
python -m compileall src\dashboard -q
python -m pytest -q
```
