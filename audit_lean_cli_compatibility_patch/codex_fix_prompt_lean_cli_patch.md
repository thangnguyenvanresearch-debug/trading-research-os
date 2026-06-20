# Follow-up Prompt - Optional LEAN Runtime Diagnostics

This is optional future work, not required remediation.

You are Codex working in:

`D:\AI2\QuantGit\trading-research-os`

TASK MODE:
LEAN Docker/runtime diagnostics only.

Do not run `lean login`.
Do not add QuantConnect cloud credentials.
Do not add brokerage configs.
Do not enable live trading.
Do not enable futures.
Do not enable leverage.
Do not place real orders.
Do not use OpenAI API or ChatGPT OAuth.

Current verified state:

- LEAN CLI is installed in `.venv-openbb`.
- Version: `lean 1.0.225`.
- Project detects `.venv-openbb\Scripts\lean.exe`.
- Runner passes `--lean-config`.
- Generated `lean.json` is local-only with `live-mode=false`.
- Skip-run works.
- Tests pass: `104 passed`.
- Executable run `lean_bt_f4d0947fa6ef` timed out after 900 seconds.
- No result/statistics files were produced.
- Metrics table is empty, no fake metrics.

Goals:

1. Improve LEAN status diagnostics:
   - split `docker_cli_available` and `docker_daemon_available`.
   - use bounded `docker info` check.
   - dashboard should distinguish Docker CLI installed vs daemon running.

2. Diagnose executable timeout without credentials:
   - do not run long unbounded jobs.
   - inspect generated project layout.
   - inspect LEAN CLI command requirements.
   - check Docker image pull/cache/runtime logs if safe.
   - keep timeout bounded.

3. If an obvious local-only compatibility fix exists:
   - make the smallest patch.
   - no cloud login.
   - no brokerage credentials.
   - no live mode.
   - no futures/leverage.
   - no real orders.

4. Add tests for any change.

Run:

```powershell
.\.venv-openbb\Scripts\python.exe -m compileall src scripts -q
.\.venv-openbb\Scripts\python.exe -m compileall src\dashboard -q
.\.venv-openbb\Scripts\python.exe -m pytest -q
```

Expected:

- no safety regressions.
- executable LEAN remains clearly marked verified or not verified.
- no fake metrics.
