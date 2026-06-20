from __future__ import annotations

import http.client
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from core.config_loader import load_config


DEFAULT_LOCAL_AI_CONFIG = {
    "enabled": True,
    "provider": "ollama",
    "base_url": "http://localhost:11434",
    "model": "qwen2.5:3b",
    "timeout_seconds": 180,
    "retry_attempts": 2,
    "retry_backoff_seconds": 3,
    "temperature": 0.2,
    "safe_mode": True,
    "allow_external_api": False,
    "allow_openai_api": False,
    "allow_chatgpt_oauth": False,
    "allow_browser_automation": False,
}


@dataclass(frozen=True)
class LocalAIStatus:
    provider: str
    base_url: str
    model: str
    available: bool
    safe_mode: bool
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "base_url": self.base_url,
            "model": self.model,
            "available": self.available,
            "safe_mode": self.safe_mode,
            "error": self.error,
        }


def get_local_ai_status(config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return Ollama-compatible local AI status without crashing when unavailable."""
    active = _local_ai_config(config)
    provider = str(active.get("provider", "ollama"))
    base_url = _normalize_base_url(str(active.get("base_url", "http://localhost:11434")))
    model = str(active.get("model", "llama3.1:8b"))
    safe_mode = bool(active.get("safe_mode", True))
    policy_error = _endpoint_policy_error(base_url, active)

    if provider != "ollama":
        return LocalAIStatus(provider, base_url, model, False, safe_mode, "Only ollama provider is supported.").as_dict()
    if policy_error:
        return LocalAIStatus(provider, base_url, model, False, safe_mode, policy_error).as_dict()

    try:
        _http_get_json(f"{base_url}/api/version", timeout=min(_timeout(active), 5))
    except Exception as exc:
        return LocalAIStatus(provider, base_url, model, False, safe_mode, f"{type(exc).__name__}: {exc}").as_dict()
    return LocalAIStatus(provider, base_url, model, True, safe_mode, None).as_dict()


def generate_with_local_ai(prompt: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Generate a local research response through Ollama /api/generate."""
    active = _local_ai_config(config)
    provider = str(active.get("provider", "ollama"))
    base_url = _normalize_base_url(str(active.get("base_url", "http://localhost:11434")))
    model = str(active.get("model", "llama3.1:8b"))
    safe_mode = bool(active.get("safe_mode", True))
    started = time.perf_counter()
    policy_error = _endpoint_policy_error(base_url, active)

    if provider != "ollama":
        return _generation_result("error", "", "Only ollama provider is supported.", provider, model, started)
    if policy_error:
        return _generation_result("error", "", policy_error, provider, model, started)
    preflight = preflight_local_ai(active)
    if preflight["status"] != "ok":
        result = _generation_result("error", "", str(preflight["error"]), provider, model, started)
        result["preflight"] = preflight
        result["attempts_used"] = 0
        result["retry_attempts_used"] = 0
        return result

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": float(active.get("temperature", 0.2))},
    }
    max_retries = max(0, int(active.get("retry_attempts", 0)))
    backoff = max(0.0, float(active.get("retry_backoff_seconds", 0)))
    attempts_allowed = max_retries + 1
    last_error: str | None = None
    for attempt in range(1, attempts_allowed + 1):
        try:
            response = _http_post_json(f"{base_url}/api/generate", payload, timeout=_timeout(active))
            response_text = str(response.get("response", ""))
            if not response_text.strip():
                result = _generation_result("error", "", "Local AI returned an empty response.", provider, model, started)
            else:
                result = _generation_result("ok", response_text, None, provider, model, started)
            result["preflight"] = preflight
            result["attempts_used"] = attempt
            result["retry_attempts_used"] = attempt - 1
            return result
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            if not _is_transient_local_error(exc) or attempt >= attempts_allowed:
                break
            if backoff:
                time.sleep(backoff)
    result = _generation_result("error", "", last_error or "Local AI generation failed.", provider, model, started)
    result["preflight"] = preflight
    result["attempts_used"] = attempts_allowed
    result["retry_attempts_used"] = max(0, attempts_allowed - 1)
    return result


def preflight_local_ai(config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Check Ollama availability and requested model before a generation call."""
    active = _local_ai_config(config)
    provider = str(active.get("provider", "ollama"))
    base_url = _normalize_base_url(str(active.get("base_url", "http://localhost:11434")))
    model = str(active.get("model", "llama3.1:8b"))
    policy_error = _endpoint_policy_error(base_url, active)
    if provider != "ollama":
        return _preflight_result("error", provider, model, False, False, "Only ollama provider is supported.")
    if policy_error:
        return _preflight_result("error", provider, model, False, False, policy_error)
    try:
        _http_get_json(f"{base_url}/api/version", timeout=min(_timeout(active), 5))
    except Exception as exc:
        return _preflight_result("error", provider, model, False, False, f"{type(exc).__name__}: {exc}")
    try:
        tags = _http_get_json(f"{base_url}/api/tags", timeout=min(_timeout(active), 10))
    except Exception as exc:
        return _preflight_result("error", provider, model, True, False, f"Unable to list Ollama models: {type(exc).__name__}: {exc}")
    available_models = _model_names(tags)
    if model not in available_models:
        return _preflight_result(
            "error",
            provider,
            model,
            True,
            False,
            f"Requested local model is not installed: {model}. Pull it with: ollama pull {model}",
        )
    return _preflight_result("ok", provider, model, True, True, None)


def _generation_result(
    status: str,
    response_text: str,
    error: str | None,
    provider: str,
    model: str,
    started: float,
) -> dict[str, Any]:
    return {
        "status": status,
        "response_text": response_text,
        "error": error,
        "provider": provider,
        "model": model,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
    }


def _preflight_result(
    status: str,
    provider: str,
    model: str,
    ollama_available: bool,
    model_available: bool,
    error: str | None,
) -> dict[str, Any]:
    return {
        "status": status,
        "provider": provider,
        "model": model,
        "ollama_available": ollama_available,
        "model_available": model_available,
        "error": error,
    }


def _model_names(tags_response: dict[str, Any]) -> set[str]:
    names: set[str] = set()
    for item in tags_response.get("models", []):
        if isinstance(item, dict):
            name = item.get("name") or item.get("model")
            if name:
                names.add(str(name))
    return names


def _is_transient_local_error(exc: Exception) -> bool:
    if isinstance(exc, (http.client.RemoteDisconnected, ConnectionResetError, TimeoutError, urllib.error.URLError)):
        return True
    cause = getattr(exc, "__cause__", None)
    return isinstance(cause, (http.client.RemoteDisconnected, ConnectionResetError, TimeoutError, urllib.error.URLError))


def _local_ai_config(config: dict[str, Any] | None = None) -> dict[str, Any]:
    active = dict(DEFAULT_LOCAL_AI_CONFIG)
    if config is None:
        try:
            active.update(load_config("local_ai"))
        except FileNotFoundError:
            pass
    else:
        active.update(config)
    return active


def _timeout(config: dict[str, Any]) -> float:
    return float(config.get("timeout_seconds", 120))


def _normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def _is_local_base_url(base_url: str) -> bool:
    parsed = urllib.parse.urlparse(base_url)
    host = (parsed.hostname or "").lower()
    return parsed.scheme in {"http", "https"} and host in {"localhost", "127.0.0.1", "::1"}


def _endpoint_policy_error(base_url: str, config: dict[str, Any]) -> str | None:
    parsed = urllib.parse.urlparse(base_url)
    host = (parsed.hostname or "").lower()
    if _is_forbidden_cloud_host(host):
        return "OpenAI and ChatGPT endpoints are never allowed for Local AI Mode."
    if _is_local_base_url(base_url):
        return None
    if bool(config.get("safe_mode", True)):
        return "Safe mode rejects non-local Local AI base_url."
    if not bool(config.get("allow_external_api", False)):
        return "allow_external_api is false; non-local Local AI base_url is rejected."
    return None


def _is_forbidden_cloud_host(host: str) -> bool:
    return host == "api.openai.com" or host.endswith(".openai.com") or host == "chatgpt.com" or host.endswith(".chatgpt.com")


def _http_get_json(url: str, timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8") or "{}")


def _http_post_json(url: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama HTTP {exc.code}: {body_text[:500]}") from exc
