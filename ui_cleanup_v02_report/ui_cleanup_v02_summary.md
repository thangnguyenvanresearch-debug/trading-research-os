# UI Cleanup v0.2 Summary

## Result

Focused Streamlit UX cleanup completed for the private research-only dashboard.

## Implemented

- Market Cockpit no longer imports Plotly as a hard dependency.
- Missing Plotly now shows: `Plotly is not installed; showing native Streamlit fallback.`
- Native fallback renders close/EMA lines and keeps OHLC details in an expander.
- Decision wording now uses `Latest Research Decision`, `Research Action`, and `Risk Gate Result`.
- Rejections are framed as `Rejected by Risk Gate`.
- Engine cards now use `Live execution allowed` instead of `Safe for live`.
- Control Center has a concise `What this means` section and moves raw registry/run/safety tables into expanders.
- Sidebar includes a page-group guide without changing Streamlit routing.
- Backtest, Freqtrade, Local AI, LEAN, and Qlib pages now show summary metrics before bounded tables/expanders.
- Local AI unavailable state includes reason, `ollama serve`, `ollama list`, expected `qwen2.5:3b`, and disables the run button.

## Validation

- Compile `src scripts`: passed.
- Compile dashboard: passed.
- Focused UX tests: `4 passed`.
- Full pytest: `141 passed`.
- Health check: passed.
- OpenBB rows: `2230`.
- Safety unsafe count: `0`.
- Unsafe dashboard control hits: `0`.
- Runtime live/futures/leverage/order enablement hits: `0`.
- Streamlit HTTP smoke: `200`.
- Streamlit process stopped after verification.
- Visual browser automation: not verified because the in-app browser runtime could not initialize in this session.

## Remaining Issues

- Manual visual inspection is still recommended.
- Local AI runtime is currently unavailable until Ollama is started.
- LEAN executable backtest remains unverified.
- Qlib trainer remains unavailable.
- SQLite fallback remains active because DuckDB is not installed.
