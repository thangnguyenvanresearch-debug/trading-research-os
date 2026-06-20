# Optional Follow-Up Prompt For Codex

Use this only after installing LEAN CLI locally. This is optional future development, not a required bugfix.

```text
You are Codex working in D:\AI2\QuantGit\trading-research-os.

TASK MODE:
Verify and harden executable local LEAN CLI backtests.

Do not enable live trading.
Do not add brokerage credentials.
Do not add QuantConnect cloud login.
Do not use OpenAI API.
Do not place real orders.
Do not enable futures or leverage.

Context:
LEAN research-only integration audit was accepted with minor followups.
Remaining issue: LEAN CLI was unavailable during audit, so executable LEAN backtest was not verified.

Tasks:
1. Check `lean --version` and Docker availability.
2. Run:
   python scripts/run_lean_backtest.py --symbols AAPL MSFT --provider yfinance --interval 1d --strategy-name equal_weight_demo
3. If LEAN CLI fails due project structure/data format, make the smallest local-only fix.
4. Do not add cloud login or brokerage config.
5. Verify:
   - run status completed or clear failed reason
   - report under reports/lean/
   - DB record in lean_backtest_runs
   - metrics parsed only if present
   - no fake metrics
6. Re-run:
   python -m compileall src scripts -q
   python -m pytest -q
7. Safety grep for OpenAI/ChatGPT/broker/live/order/futures/leverage terms.

Final response:
- files changed
- LEAN CLI execution result
- run_id/report_path
- metrics parsed
- remaining issues
- safety confirmation
```

