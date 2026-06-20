# Follow-up Prompt - Control Center Accuracy Cleanup

You are Codex working in:

`D:\AI2\QuantGit\trading-research-os`

TASK MODE:
Focused Control Center accuracy cleanup.

Do not enable live trading.
Do not enable futures.
Do not enable leverage.
Do not add brokerage configs.
Do not add cloud credentials.
Do not place real orders.
Do not use OpenAI API or ChatGPT OAuth.

Audit result:

- Control Center accepted with minor followups.
- Tests pass: `129 passed`.
- Safety is OK.
- Remaining issues are status wording/read-only accuracy.

Fix only:

1. LEAN status accuracy:
   - In `src/dashboard/control_center.py`, do not report LEAN as simply `ready`.
   - Add fields:
     - `cli_detected`
     - `skeleton_available`
     - `executable_verified`
     - `latest_executable_status`
   - If latest executable run failed/timeout or no completed run exists, show `cli_detected_executable_unverified`.
   - Page card should not imply executable backtest is ready.

2. Daily status wording:
   - Rename `daily_scheduler` to `latest_daily_run` in Control Center status.
   - If actual Windows Task Scheduler is not queried, show scheduler state as `not verified`.

3. Warning/error summaries:
   - Truncate displayed warning/error summaries to a reasonable length, e.g. 240 chars.
   - Keep full JSON available where already stored.

4. CLI DB behavior:
   - Either document that `initialize_database()` may initialize schema, or avoid calling it in the pure status report path if safe.

5. README:
   - In Research Control Center section, explicitly say:
     - LEAN executable backtest remains unverified until Docker/runtime succeeds.
     - Qlib true trainer remains future work while package is missing.

6. Tests:
   - Add tests that LEAN status does not overstate readiness.
   - Add tests that Daily status is latest DB run, not scheduler state.
   - Add tests for warning/error truncation.

Run:

```powershell
python -m compileall src scripts -q
python -m compileall src\dashboard -q
python -m pytest -q
python scripts\report_control_center_status.py
```
