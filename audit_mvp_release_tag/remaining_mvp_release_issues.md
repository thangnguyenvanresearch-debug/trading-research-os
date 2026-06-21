# Remaining MVP Release Issues

## Medium

None affecting research-only safety or private repository push.

## Low / Operational

| Issue | Evidence | Impact | Recommendation |
|---|---|---|---|
| Scheduled task not verified | `Get-ScheduledTask` returned `TASK_NOT_FOUND`. | Daily automation is not currently proven active on this machine. | Re-register or verify task before demoing scheduled automation. |
| Venv ignore is local-only | `.venv-openbb/` is in `.git/info/exclude`, not committed `.gitignore`. | Fresh clones do not inherit this protection. | Add `.venv-openbb/`, `.ruff_cache/`, and runtime log patterns in a future hygiene commit. |
| Ollama currently unavailable | Health JSON reported Local AI `unavailable`. | Local AI demo button/CLI will fail gracefully until service starts. | Start Ollama and verify `qwen2.5:3b` before demo. |
| Dashboard visual pass manual | HTTP 200 and source inspection passed; browser UI was not automated. | Minor residual UI rendering risk. | Perform a manual Control Center visual check. |
| Optional engine limitations | LEAN executable unverified; Qlib package/trainer unavailable; DuckDB absent. | Limits optional engine demonstrations, not core safety. | Keep these as documented future work. |
