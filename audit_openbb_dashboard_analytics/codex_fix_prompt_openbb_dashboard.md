# Codex Fix Prompt OpenBB Dashboard

No required remediation is needed. Use this optional prompt only for future polish.

```
You are Codex working in D:\AI2\QuantGit\trading-research-os.

TASK MODE: Optional OpenBB dashboard polish.

Do not enable live trading, futures, leverage, real orders, API key forms, or exchange configs. Do not fetch external data from dashboard page load.

Optional improvements:
1. Add interval normalization in `src/analytics/openbb_analytics.py` so daily volatility recognizes values such as `1d`, `1D`, `daily`, or provider-specific aliases.
2. Add a visual smoke test or documented manual checklist for `src/dashboard/pages/10_openbb_ingestion.py`.
3. Add optional `--output ""` behavior to `scripts/report_openbb_analytics.py` if users want console-only reports.

Run safe checks:
python -m compileall src scripts -q
python -m pytest -q

Keep analytics descriptive and local-DB-only.
```
