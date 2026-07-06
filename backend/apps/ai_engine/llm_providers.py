"""Multi-provider LLM abstraction layer.

Supports: Anthropic (Claude), OpenAI, Google Gemini, Groq.
Provider selection via settings.AI_DEFAULT_PROVIDER or per-call override,
with automatic fallback chain and unified response format.
"""
import os
import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import requests

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    raw: dict = field(default_factory=dict)


class LLMProvider(ABC):
    name = "base"
    default_model = ""
    timeout = 60

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.environ.get(f"{self.name.upper()}_API_KEY", "")
        self.model = model or self.default_model

    @abstractmethod
    def complete(self, prompt: str, system: str = "", max_tokens: int = 1024,
                 temperature: float = 0.3) -> LLMResponse: ...

    def is_configured(self) -> bool:
        return bool(self.api_key)


class AnthropicProvider(LLMProvider):
    name = "anthropic"
    default_model = "claude-sonnet-4-6"

    def complete(self, prompt, system="", max_tokens=1024, temperature=0.3):
        t0 = time.monotonic()
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            payload["system"] = system
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=payload, timeout=self.timeout,
        )
        r.raise_for_status()
        data = r.json()
        return LLMResponse(
            text="".join(b.get("text", "") for b in data.get("content", [])),
            provider=self.name, model=self.model,
            input_tokens=data.get("usage", {}).get("input_tokens", 0),
            output_tokens=data.get("usage", {}).get("output_tokens", 0),
            latency_ms=int((time.monotonic() - t0) * 1000), raw=data,
        )


class OpenAIProvider(LLMProvider):
    name = "openai"
    default_model = "gpt-4o-mini"
    endpoint = "https://api.openai.com/v1/chat/completions"

    def complete(self, prompt, system="", max_tokens=1024, temperature=0.3):
        t0 = time.monotonic()
        messages = ([{"role": "system", "content": system}] if system else []) + [
            {"role": "user", "content": prompt}
        ]
        r = requests.post(
            self.endpoint,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "messages": messages,
                  "max_tokens": max_tokens, "temperature": temperature},
            timeout=self.timeout,
        )
        r.raise_for_status()
        data = r.json()
        usage = data.get("usage", {})
        return LLMResponse(
            text=data["choices"][0]["message"]["content"],
            provider=self.name, model=self.model,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            latency_ms=int((time.monotonic() - t0) * 1000), raw=data,
        )


class GroqProvider(OpenAIProvider):
    name = "groq"
    default_model = "llama-3.3-70b-versatile"
    endpoint = "https://api.groq.com/openai/v1/chat/completions"


class GeminiProvider(LLMProvider):
    name = "gemini"
    default_model = "gemini-2.0-flash"

    def complete(self, prompt, system="", max_tokens=1024, temperature=0.3):
        t0 = time.monotonic()
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{self.model}:generateContent?key={self.api_key}")
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": temperature},
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        r = requests.post(url, json=payload, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        text = ""
        for cand in data.get("candidates", []):
            for part in cand.get("content", {}).get("parts", []):
                text += part.get("text", "")
        usage = data.get("usageMetadata", {})
        return LLMResponse(
            text=text, provider=self.name, model=self.model,
            input_tokens=usage.get("promptTokenCount", 0),
            output_tokens=usage.get("candidatesTokenCount", 0),
            latency_ms=int((time.monotonic() - t0) * 1000), raw=data,
        )


PROVIDERS = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "groq": GroqProvider,
}


class MultiProviderLLM:
    """Unified entry point with fallback chain across configured providers."""

    def __init__(self, order: list[str] | None = None):
        from django.conf import settings
        self.order = order or getattr(
            settings, "AI_PROVIDER_ORDER", ["anthropic", "openai", "gemini", "groq"]
        )

    def complete(self, prompt: str, system: str = "", **kwargs) -> LLMResponse:
        last_err = None
        for name in self.order:
            provider = PROVIDERS[name]()
            if not provider.is_configured():
                continue
            try:
                resp = provider.complete(prompt, system=system, **kwargs)
                logger.info("llm ok provider=%s model=%s latency=%sms",
                            resp.provider, resp.model, resp.latency_ms)
                return resp
            except Exception as exc:  # noqa: BLE001 - fallback chain
                last_err = exc
                logger.warning("llm provider %s failed: %s — falling back", name, exc)
        raise RuntimeError(f"All LLM providers failed. Last error: {last_err}")
