# UI Cleanup v0.2 Details

## Task Workflow

1. Baseline Git and health check.
2. Plotly-safe Market Cockpit fallback.
3. Research-only wording cleanup.
4. Control Center layout cleanup.
5. Sidebar guide and table density reduction.
6. Local AI unavailable guidance.
7. Compile, test, health and safety validation.
8. Streamlit HTTP/browser smoke.

## Baseline

```text
branch=main
latest_commit=c3154f3 docs: add private repo push report
tags=v0.1.0-research-only-mvp, v0.1.1-research-only-hygiene
worktree=clean
```

Health baseline:

```text
openbb_total_rows=2230
local_ai=unavailable
latest_daily_run=daily_ccd5abf71f95 (completed_with_warnings)
lean=executable_failed_timeout / latest artifact skeleton_created
qlib=missing / latest run unavailable
safety_unsafe_count=0
```

## Market Cockpit

`src/dashboard/components/charts.py` now catches `ImportError` for Plotly. A focused test blocks Plotly imports and verifies that the component imports, emits the required warning, and calls native `st.line_chart`.

No package was installed.

## Wording

Display-only labels changed:

- Latest Signal -> Latest Research Decision
- Signal -> Research Action
- Permission -> Risk Gate Result
- Safe for live -> Live execution allowed
- rejected -> Rejected by Risk Gate where displayed

Stored database values and trading/risk logic were not changed.

## Control Center

Top cards and caveats remain. Added user-oriented explanations for OpenBB, Ollama, latest daily DB run, LEAN, Qlib and safety. Engine Registry, Latest Runs and Artifacts, Safety Details, duplicate checks and raw JSON are collapsed by default.

## Navigation And Tables

Native Streamlit page routing and filenames remain unchanged. A sidebar page guide provides Core, Research, Data/AI, and Engines/Labs groupings.

Dense pages now provide summary metrics and bounded tables under expanders. Full records remain scrollable and accessible.

## Local AI

When unavailable, the page displays the runtime error/reason and local commands:

```powershell
ollama serve
ollama list
```

Expected model is `qwen2.5:3b`. The local research button is disabled until the status check succeeds. The app does not auto-start Ollama.

## Commands And Outputs

```text
python -m compileall src scripts -q                 passed
python -m compileall src/dashboard -q               passed
python -m pytest tests/test_dashboard_ux.py -q      4 passed
python -m pytest -q                                 141 passed
python scripts/health_check.py                      passed; unsafe count 0
```

Safety scan:

```text
unsafe_control_hits=0
live_enablement_hits=0
```

Streamlit:

```text
http://localhost:8501 -> 200
duplicate listener before start -> none
server stopped after smoke -> confirmed
```

In-app browser visual automation could not initialize because required browser runtime metadata was unavailable. Per the task fallback rule, HTTP, source inspection, compile, and focused Plotly-missing tests were used. Visual check is recorded as not verified.
