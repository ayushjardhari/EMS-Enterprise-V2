"""Minimal client for any OpenAI-compatible chat-completions API (Groq, Ollama, OpenRouter, ...).

Switching provider is a configuration change (LLM_BASE_URL, LLM_MODEL, LLM_API_KEY).
Every failure is raised as LLMError so callers can fall back to a non-LLM answer.
"""
import httpx

from app.core.config import settings


class LLMError(Exception):
    """The LLM call failed (not configured, network, HTTP error, rate limit, bad response)."""


class LLMRateLimited(LLMError):
    """HTTP 429: the free-plan limits were hit."""


class LLMClient:
    def __init__(self, base_url: str | None = None, api_key: str | None = None, model: str | None = None,
                 timeout: float | None = None, transport: httpx.BaseTransport | None = None):
        self.base_url = (base_url or settings.LLM_BASE_URL).rstrip("/")
        self.api_key = settings.LLM_API_KEY if api_key is None else api_key
        self.model = model or settings.LLM_MODEL
        self.timeout = timeout or settings.LLM_TIMEOUT_SECONDS
        self._transport = transport

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def chat(self, messages: list[dict], max_tokens: int = 500, temperature: float = 0.2) -> str:
        if not self.configured:
            raise LLMError("LLM_API_KEY is not set")
        body = {"model": self.model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
        if settings.LLM_REASONING_EFFORT:
            body["reasoning_effort"] = settings.LLM_REASONING_EFFORT
        try:
            with httpx.Client(timeout=self.timeout, transport=self._transport) as client:
                response = client.post(f"{self.base_url}/chat/completions", json=body,
                                       headers={"Authorization": f"Bearer {self.api_key}"})
        except httpx.HTTPError as exc:
            raise LLMError(f"network error: {exc.__class__.__name__}") from exc
        if response.status_code == 429:
            raise LLMRateLimited("rate limit reached (HTTP 429)")
        if response.status_code != 200:
            # Do not echo the response body: it can contain request details. Status code is enough.
            raise LLMError(f"HTTP {response.status_code}")
        try:
            text = response.json()["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise LLMError("unexpected response format") from exc
        if not text or not text.strip():
            raise LLMError("empty response")
        return text.strip()
