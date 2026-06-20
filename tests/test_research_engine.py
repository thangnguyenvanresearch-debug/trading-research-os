from __future__ import annotations

import json
from pathlib import Path

import core.database as database
from ai import research_engine
from ai.research_engine import build_local_ai_prompt, build_research_context, run_local_ai_research
from core.database import execute, fetch_dataframe, initialize_database, insert_dict


def test_prompt_builder_contains_safety_and_backtest_caution() -> None:
    prompt = build_local_ai_prompt("local context", "market_review")

    assert "Do not give direct buy or sell orders" in prompt
    assert "Do not treat backtests as proof of future profit" in prompt
    assert "not trading advice" in prompt


def test_research_context_works_with_empty_database(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    initialize_database()

    context, markdown = build_research_context(symbols=["AAPL"], provider="yfinance", interval="1d")

    assert context["task_type"] == "market_review"
    assert context["openbb"]["row_count"] == 0
    assert "No local OpenBB market rows" in " ".join(context["warnings"])
    assert "openbb_market_data" in context["data_sources"]
    assert "```json" in markdown


def test_research_context_works_with_mocked_openbb_rows(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    initialize_database()
    _insert_openbb_row("AAPL", "2024-01-01", 100)
    _insert_openbb_row("AAPL", "2024-01-02", 110)

    context, _ = build_research_context(symbols=["AAPL"], provider="yfinance", interval="1d")

    assert context["openbb"]["row_count"] == 2
    assert context["openbb"]["return_summary"][0]["symbol"] == "AAPL"
    assert round(float(context["openbb"]["return_summary"][0]["total_return"]), 4) == 0.1


def test_run_local_ai_research_handles_unavailable_without_crash(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    monkeypatch.setattr(research_engine, "REPORTS_DIR", tmp_path / "reports")
    initialize_database()
    monkeypatch.setattr(
        research_engine,
        "get_local_ai_status",
        lambda config=None: {
            "provider": "ollama",
            "base_url": "http://localhost:11434",
            "model": "llama3.1:8b",
            "available": False,
            "safe_mode": True,
            "error": "Ollama unavailable",
        },
    )

    result = run_local_ai_research(symbols=["AAPL"], provider="yfinance", interval="1d")

    assert result["status"] == "failed"
    assert result["error"] == "Ollama unavailable"
    stored = fetch_dataframe("SELECT memo_id, status, response_text FROM ai_research_memos")
    assert len(stored) == 1
    assert stored.iloc[0]["status"] == "failed"


def test_ai_research_memo_insert_with_mocked_local_ai_response(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    monkeypatch.setattr(research_engine, "REPORTS_DIR", tmp_path / "reports")
    initialize_database()
    _insert_openbb_row("AAPL", "2024-01-01", 100)
    monkeypatch.setattr(
        research_engine,
        "get_local_ai_status",
        lambda config=None: {
            "provider": "ollama",
            "base_url": "http://localhost:11434",
            "model": "llama3.1:8b",
            "available": True,
            "safe_mode": True,
            "error": None,
        },
    )
    monkeypatch.setattr(
        research_engine,
        "generate_with_local_ai",
        lambda prompt, config=None: {
            "status": "ok",
            "response_text": "Mock local memo",
            "error": None,
            "provider": "ollama",
            "model": "llama3.1:8b",
            "elapsed_seconds": 0.01,
        },
    )

    result = run_local_ai_research(symbols=["AAPL"], provider="yfinance", interval="1d")

    assert result["status"] == "completed"
    assert Path(result["output_path"]).exists()
    stored = fetch_dataframe("SELECT * FROM ai_research_memos")
    assert len(stored) == 1
    assert stored.iloc[0]["response_text"] == "Mock local memo"
    context = json.loads(stored.iloc[0]["source_context_json"])
    assert context["openbb"]["row_count"] == 1


def test_run_local_ai_research_uses_compact_retry_after_disconnect(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    monkeypatch.setattr(research_engine, "REPORTS_DIR", tmp_path / "reports")
    initialize_database()
    _insert_openbb_row("AAPL", "2024-01-01", 100)
    monkeypatch.setattr(
        research_engine,
        "get_local_ai_status",
        lambda config=None: {
            "provider": "ollama",
            "base_url": "http://localhost:11434",
            "model": "qwen2.5:3b",
            "available": True,
            "safe_mode": True,
            "error": None,
        },
    )
    calls = {"count": 0, "prompts": []}

    def fake_generate(prompt: str, config=None):
        calls["count"] += 1
        calls["prompts"].append(prompt)
        if calls["count"] == 1:
            return {
                "status": "error",
                "response_text": "",
                "error": "RemoteDisconnected: Remote end closed connection without response",
                "provider": "ollama",
                "model": "qwen2.5:3b",
                "elapsed_seconds": 1,
                "preflight": {"status": "ok", "model_available": True},
                "retry_attempts_used": 2,
            }
        return {
            "status": "ok",
            "response_text": "Compact memo",
            "error": None,
            "provider": "ollama",
            "model": "qwen2.5:3b",
            "elapsed_seconds": 1,
            "preflight": {"status": "ok", "model_available": True},
            "retry_attempts_used": 0,
        }

    monkeypatch.setattr(research_engine, "generate_with_local_ai", fake_generate)

    result = run_local_ai_research(symbols=["AAPL"], provider="yfinance", interval="1d")

    assert result["status"] == "completed"
    assert result["compact_retry_used"] is True
    assert result["retry_attempts_used"] == 0
    assert calls["count"] == 2
    assert len(calls["prompts"][1]) <= len(calls["prompts"][0])
    stored = fetch_dataframe("SELECT response_text, metadata_json FROM ai_research_memos")
    metadata = json.loads(stored.iloc[0]["metadata_json"])
    assert stored.iloc[0]["response_text"] == "Compact memo"
    assert metadata["compact_retry_used"] is True


def test_research_engine_source_has_no_cloud_ai_or_browser_backend_strings() -> None:
    source = research_engine.__loader__.get_source(research_engine.__name__)

    assert "OPENAI_API_KEY" not in source
    assert "api.openai.com" not in source
    assert "chatgpt.com/auth" not in source
    assert "playwright" not in source
    assert "selenium" not in source


def _insert_openbb_row(symbol: str, timestamp: str, close: float) -> None:
    insert_dict(
        "openbb_market_data",
        {
            "id": f"{symbol}_{timestamp}",
            "symbol": symbol,
            "asset_class": "equity",
            "provider": "yfinance",
            "interval": "1d",
            "timestamp": timestamp,
            "open": close,
            "high": close + 1,
            "low": close - 1,
            "close": close,
            "volume": 1000,
            "adjusted_close": close,
            "source": "openbb_adapter",
            "retrieved_at": "2026-01-01T00:00:00+00:00",
            "metadata_json": "{}",
        },
    )


def test_research_context_can_include_backtests_risk_and_decisions(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(database, "database_path", lambda: tmp_path / "test.sqlite")
    initialize_database()
    execute(
        """
        INSERT OR REPLACE INTO backtest_metrics
        (run_id, strategy_id, total_return, max_drawdown, trade_count, profit_factor, created_at)
        VALUES ('bt_test', 'strategy_test', 0.1, 0.05, 20, 1.3, '2026-01-01T00:00:00+00:00')
        """
    )
    execute(
        """
        INSERT OR REPLACE INTO risk_reviews
        (review_id, strategy_id, run_id, status, flags, reviewed_at)
        VALUES ('rr_test', 'strategy_test', 'bt_test', 'watchlist', '[]', '2026-01-01T00:00:00+00:00')
        """
    )
    execute(
        """
        INSERT OR REPLACE INTO decisions
        (decision_id, symbol, strategy_id, strategy_name, run_id, signal, permission, score, regime, reasons, risk_flags, created_at)
        VALUES ('dec_test', 'AAPL', 'strategy_test', 'Strategy Test', 'bt_test', 'WAIT', 'WATCHLIST', 55, 'unknown', '[]', '[]', '2026-01-01T00:00:00+00:00')
        """
    )

    context, _ = build_research_context(
        symbols=["AAPL"],
        include_backtests=True,
        include_risk=True,
        include_decisions=True,
    )

    assert context["backtests"][0]["run_id"] == "bt_test"
    assert context["risk_reviews"][0]["review_id"] == "rr_test"
    assert context["decisions"][0]["decision_id"] == "dec_test"


def test_missing_optional_context_table_returns_empty_with_warning(monkeypatch) -> None:
    def missing_table(query: str, params: tuple = ()):
        raise RuntimeError("no such table: risk_reviews")

    monkeypatch.setattr(research_engine, "fetch_dataframe", missing_table)

    context, _ = build_research_context(include_openbb=False, include_risk=True)

    assert context["risk_reviews"] == []
    assert "Optional context table missing: risk_reviews" in context["warnings"]


def test_unexpected_optional_context_query_error_is_not_silently_swallowed(monkeypatch) -> None:
    def unexpected_error(query: str, params: tuple = ()):
        raise RuntimeError("database is locked")

    monkeypatch.setattr(research_engine, "fetch_dataframe", unexpected_error)

    try:
        build_research_context(include_openbb=False, include_risk=True)
    except RuntimeError as exc:
        assert "database is locked" in str(exc)
    else:
        raise AssertionError("Unexpected DB errors should not be silently swallowed.")
