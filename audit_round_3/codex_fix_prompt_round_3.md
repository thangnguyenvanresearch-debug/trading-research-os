# Codex Fix Prompt Round 3

Use this prompt only for a small follow-up cleanup pass. Do not rewrite the project.

```text
You are Codex working in D:\AI2\QuantGit\trading-research-os.

Task mode: focused cleanup after Round 3 audit.

Do not enable live trading.
Do not enable futures.
Do not enable leverage.
Do not place real orders.
Do not add API key forms or real exchange configs.

Round 3 audit verdict: accepted.
Only address the verified low-priority issues below.

1. Add missing test coverage for keyword negative shift.

File:
tests/test_no_lookahead.py

Add a pytest case confirming:
analyze_python_lookahead_risk("x = df.close.shift(periods=-1)")
returns has_risk == True and includes a negative pandas shift pattern.

2. Persist inspected look-ahead paths into risk review flags.

File:
src/risk_brain/risk_gate.py

Current behavior:
_lookahead_review() returns inspected_paths, but run_risk_reviews() only stores issues/warnings in flags.

Change:
When lookahead_review has inspected_paths and either issues or warnings are present, append human-readable flags such as:
"Look-ahead inspected path: <path>"

Keep this readable and do not expose secrets.

3. Optional: standardize FinceptTerminal status taxonomy.

Files:
configs/engine_registry.yaml
README.md if needed
Possibly add a tiny status helper only if it does not create architecture churn.

Current behavior:
FinceptTerminal is honestly marked mentioned_only/future, but mentioned_only is not part of ALLOWED_ENGINE_STATUSES.

Acceptable fixes:
- Change config status to scaffold_only with current_capability/next_step language, or
- Add mentioned_only to ALLOWED_ENGINE_STATUSES and tests if you want to preserve the wording.

Do not implement FinceptTerminal integration.

After changes, run:
python -m compileall src scripts -q
python -m pytest -q

Report files changed and confirm live trading/futures/leverage/real orders remain disabled.
```

