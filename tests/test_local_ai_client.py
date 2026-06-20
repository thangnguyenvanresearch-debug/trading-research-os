from __future__ import annotations

import http.client

import pytest

from ai import local_ai_client
from ai.local_ai_client import generate_with_local_ai, get_local_ai_status


def test_local_ai_unavailable_returns_safe_status(monkeypatch) -> None:
    def fail_get(url: str, timeout: float) -> dict:
        raise ConnectionRefusedError("ollama is not running")

    monkeypatch.setattr(local_ai_client, "_http_get_json", fail_get)

    status = get_local_ai_status({"base_url": "http://localhost:11434", "model": "llama3.1:8b"})

    assert status["available"] is False
    assert status["provider"] == "ollama"
    assert "ollama is not running" in status["error"]


def test_non_localhost_base_url_rejected_in_safe_mode() -> None:
    result = generate_with_local_ai(
        "hello",
        {
            "provider": "ollama",
            "base_url": "https://example.com",
            "model": "llama3.1:8b",
            "safe_mode": True,
        },
    )

    assert result["status"] == "error"
    assert "non-local" in result["error"]


def test_non_localhost_rejected_when_external_api_not_allowed_even_without_safe_mode() -> None:
    result = generate_with_local_ai(
        "hello",
        {
            "provider": "ollama",
            "base_url": "https://local-lan-model.example",
            "model": "llama3.1:8b",
            "safe_mode": False,
            "allow_external_api": False,
        },
    )

    assert result["status"] == "error"
    assert "allow_external_api is false" in result["error"]


def test_localhost_allowed_with_safe_mode(monkeypatch) -> None:
    monkeypatch.setattr(local_ai_client, "_http_get_json", lambda url, timeout: {"version": "test"})

    status = get_local_ai_status({"base_url": "http://localhost:11434", "safe_mode": True})

    assert status["available"] is True


def test_localhost_allowed_without_safe_mode(monkeypatch) -> None:
    monkeypatch.setattr(local_ai_client, "_http_get_json", lambda url, timeout: {"version": "test"})

    status = get_local_ai_status({"base_url": "http://127.0.0.1:11434", "safe_mode": False})

    assert status["available"] is True


def test_external_endpoint_allowed_only_when_explicitly_enabled_and_not_forbidden(monkeypatch) -> None:
    monkeypatch.setattr(local_ai_client, "_http_get_json", lambda url, timeout: {"version": "test"})

    status = get_local_ai_status(
        {
            "base_url": "https://local-model-gateway.example",
            "safe_mode": False,
            "allow_external_api": True,
        }
    )

    assert status["available"] is True


@pytest.mark.parametrize("base_url", ["https://api.openai.com", "https://chatgpt.com/auth"])
def test_openai_and_chatgpt_endpoints_are_never_allowed(base_url: str) -> None:
    status = get_local_ai_status(
        {
            "base_url": base_url,
            "safe_mode": False,
            "allow_external_api": True,
        }
    )

    assert status["available"] is False
    assert "never allowed" in status["error"]


def test_generate_with_mocked_ollama_response(monkeypatch) -> None:
    def fake_get(url: str, timeout: float) -> dict:
        if url.endswith("/api/tags"):
            return {"models": [{"name": "qwen2.5:7b"}]}
        return {"version": "test"}

    def fake_post(url: str, payload: dict, timeout: float) -> dict:
        assert url == "http://localhost:11434/api/generate"
        assert payload["stream"] is False
        assert payload["model"] == "qwen2.5:7b"
        return {"response": "Local memo text"}

    monkeypatch.setattr(local_ai_client, "_http_get_json", fake_get)
    monkeypatch.setattr(local_ai_client, "_http_post_json", fake_post)

    result = generate_with_local_ai(
        "summarize",
        {"base_url": "http://localhost:11434", "model": "qwen2.5:7b", "temperature": 0.1},
    )

    assert result["status"] == "ok"
    assert result["response_text"] == "Local memo text"


def test_generate_retries_transient_disconnect_then_succeeds(monkeypatch) -> None:
    calls = {"post": 0, "sleep": 0}

    def fake_get(url: str, timeout: float) -> dict:
        if url.endswith("/api/tags"):
            return {"models": [{"name": "qwen2.5:3b"}]}
        return {"version": "test"}

    def fake_post(url: str, payload: dict, timeout: float) -> dict:
        calls["post"] += 1
        if calls["post"] == 1:
            raise http.client.RemoteDisconnected("closed connection")
        return {"response": "Recovered memo"}

    monkeypatch.setattr(local_ai_client, "_http_get_json", fake_get)
    monkeypatch.setattr(local_ai_client, "_http_post_json", fake_post)
    monkeypatch.setattr(local_ai_client.time, "sleep", lambda seconds: calls.update(sleep=calls["sleep"] + 1))

    result = generate_with_local_ai(
        "memo",
        {"base_url": "http://localhost:11434", "model": "qwen2.5:3b", "retry_attempts": 2},
    )

    assert result["status"] == "ok"
    assert result["response_text"] == "Recovered memo"
    assert result["retry_attempts_used"] == 1
    assert calls["post"] == 2


def test_generate_fails_fast_when_model_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        local_ai_client,
        "_http_get_json",
        lambda url, timeout: {"models": [{"name": "other-model"}]} if url.endswith("/api/tags") else {"version": "test"},
    )
    monkeypatch.setattr(
        local_ai_client,
        "_http_post_json",
        lambda url, payload, timeout: (_ for _ in ()).throw(AssertionError("generate should not be called")),
    )

    result = generate_with_local_ai(
        "memo",
        {"base_url": "http://localhost:11434", "model": "qwen2.5:3b", "retry_attempts": 2},
    )

    assert result["status"] == "error"
    assert "not installed" in result["error"]
    assert result["preflight"]["model_available"] is False


def test_forbidden_host_is_not_retried(monkeypatch) -> None:
    monkeypatch.setattr(
        local_ai_client,
        "_http_post_json",
        lambda url, payload, timeout: (_ for _ in ()).throw(AssertionError("generate should not be called")),
    )

    result = generate_with_local_ai(
        "memo",
        {
            "base_url": "https://api.openai.com",
            "model": "qwen2.5:3b",
            "safe_mode": False,
            "allow_external_api": True,
            "retry_attempts": 2,
        },
    )

    assert result["status"] == "error"
    assert "never allowed" in result["error"]


def test_local_ai_client_has_no_order_surface() -> None:
    names = set(dir(local_ai_client))

    assert not {"create_order", "place_order", "market_order", "limit_order"} & names


@pytest.mark.parametrize("forbidden", ["OPENAI_API_KEY", "api.openai.com/v1", "chatgpt.com/auth"])
def test_local_ai_client_has_no_openai_or_chatgpt_backend_integration_strings(forbidden: str) -> None:
    source = local_ai_client.__loader__.get_source(local_ai_client.__name__)

    assert forbidden not in source
