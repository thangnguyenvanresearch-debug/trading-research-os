from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai.local_ai_client import get_local_ai_status  # noqa: E402
from ai.research_engine import ALLOWED_TASKS, build_research_context, build_local_ai_prompt, run_local_ai_research  # noqa: E402
from core.config_loader import load_config  # noqa: E402
from core.database import fetch_dataframe, initialize_database  # noqa: E402
from dashboard.components.tables import dataframe_or_message  # noqa: E402
from dashboard.components.ui import caveat_box, compact_dataframe, hero, metric_card, section_header, setup_page  # noqa: E402


@st.cache_data(ttl=45, show_spinner=False)
def _cached_local_ai_status(
    provider: str,
    base_url: str,
    model: str,
    safe_mode: bool,
    allow_external_api: bool,
    timeout_seconds: int,
) -> dict:
    return get_local_ai_status(
        {
            "provider": provider,
            "base_url": base_url,
            "model": model,
            "safe_mode": safe_mode,
            "allow_external_api": allow_external_api,
            "timeout_seconds": timeout_seconds,
        }
    )


initialize_database()
setup_page()
hero(
    "Local AI Research",
    "Generate research memos with a local Ollama model using only selected local context.",
    badges=[("Ollama local", "info"), ("No cloud API", "success"), ("No orders", "success")],
)
caveat_box("Local AI output is research commentary, not trading advice. It cannot place orders.", "warning")

config = load_config("local_ai")
status = _cached_local_ai_status(
    str(config.get("provider", "ollama")),
    str(config.get("base_url", "http://localhost:11434")),
    str(config.get("model", "llama3.1:8b")),
    bool(config.get("safe_mode", True)),
    bool(config.get("allow_external_api", False)),
    int(config.get("timeout_seconds", 120)),
)

status_cols = st.columns(4)
with status_cols[0]:
    metric_card("Runtime", "Available" if status["available"] else "Unavailable", (status["provider"], "success" if status["available"] else "warning"))
with status_cols[1]:
    metric_card("Model", status["model"], ("Local model", "info"))
with status_cols[2]:
    metric_card("Safe Mode", status["safe_mode"], ("Localhost enforced", "success"))
with status_cols[3]:
    metric_card("Endpoint", status["base_url"], ("Local only", "neutral"))
if not status.get("available"):
    caveat_box(f"Local AI unavailable: {status.get('error') or 'Ollama did not answer the local status check.'}", "danger")
    section_header("Start Local AI", "Run these commands in a separate PowerShell terminal")
    setup_cols = st.columns(3)
    setup_cols[0].code("ollama serve", language="powershell")
    setup_cols[1].code("ollama list", language="powershell")
    setup_cols[2].code("qwen2.5:3b", language="text")
with st.expander("Local AI runtime details", expanded=False):
    compact_dataframe(pd.DataFrame([status]), height=180)

section_header("Run Local Research", "The run control stays disabled until the local Ollama preflight succeeds")
with st.form("local_ai_research_form"):
    symbols_text = st.text_input("Symbols", value="AAPL MSFT")
    provider = st.text_input("Provider filter", value="yfinance")
    interval = st.text_input("Interval filter", value="1d")
    task_type = st.selectbox("Task type", options=sorted(ALLOWED_TASKS), index=sorted(ALLOWED_TASKS).index("market_review"))
    include_openbb = st.checkbox("Include OpenBB local market data", value=True)
    include_backtests = st.checkbox("Include latest backtest metrics", value=False)
    include_risk = st.checkbox("Include latest risk reviews", value=False)
    include_decisions = st.checkbox("Include latest decisions", value=False)
    run_clicked = st.form_submit_button("Run local AI research", disabled=not bool(status.get("available")))

symbols = [part.strip() for part in symbols_text.split() if part.strip()]
provider_filter = provider.strip() or None
interval_filter = interval.strip() or None

if run_clicked:
    result = run_local_ai_research(
        symbols=symbols,
        provider=provider_filter,
        interval=interval_filter,
        task_type=task_type,
        include_openbb=include_openbb,
        include_backtests=include_backtests,
        include_risk=include_risk,
        include_decisions=include_decisions,
        config=config,
    )
    st.success(f"Memo saved: {result['memo_id']} ({result['status']})")
    if result.get("warnings"):
        st.warning("; ".join(str(warning) for warning in result["warnings"]))
    if result.get("error"):
        st.error(str(result["error"]))
    st.code(result["output_path"])

section_header("Prompt / Context Preview")
context, context_markdown = build_research_context(
    symbols=symbols,
    provider=provider_filter,
    interval=interval_filter,
    task_type=task_type,
    include_openbb=include_openbb,
    include_backtests=include_backtests,
    include_risk=include_risk,
    include_decisions=include_decisions,
    max_context_chars=int(config.get("max_context_chars", 24000)),
)
prompt_preview = build_local_ai_prompt(context_markdown, task_type)
with st.expander("Context JSON", expanded=False):
    st.json(context)
with st.expander("Prompt Preview", expanded=False):
    st.code(prompt_preview, language="markdown")

section_header("Latest AI Research Memos", "Stored locally for review and comparison")
memos = fetch_dataframe(
    """
    SELECT memo_id, created_at, provider, model, task_type, symbols, status, warnings_json, metadata_json
    FROM ai_research_memos
    ORDER BY created_at DESC
    LIMIT 20
    """
)
memo_cols = st.columns(2)
with memo_cols[0]:
    metric_card("Stored Memos", len(memos), ("Local database", "neutral"))
with memo_cols[1]:
    latest_memo_status = str(memos.iloc[0]["status"]) if not memos.empty else "none"
    metric_card("Latest Memo", latest_memo_status, ("Research artifact", "success" if latest_memo_status == "completed" else "warning"))
with st.expander("Memo history", expanded=False):
    dataframe_or_message(memos, "No local AI research memos recorded yet.", height=320)

if not memos.empty:
    selected = st.selectbox("Memo response", options=list(memos["memo_id"]))
    memo = fetch_dataframe(
        """
        SELECT response_text, prompt_text, source_context_json, warnings_json
        FROM ai_research_memos
        WHERE memo_id = ?
        """,
        (selected,),
    )
    if not memo.empty:
        row = memo.iloc[0]
        st.markdown(str(row["response_text"]) if str(row["response_text"]).strip() else "_No response generated._")
        with st.expander("Stored prompt", expanded=False):
            st.code(str(row["prompt_text"]), language="markdown")
        with st.expander("Stored source context", expanded=False):
            try:
                st.json(json.loads(str(row["source_context_json"])))
            except Exception:
                st.code(str(row["source_context_json"]))
