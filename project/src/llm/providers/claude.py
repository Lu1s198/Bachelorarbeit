"""Anthropic Claude Provider."""

import time

from anthropic import Anthropic

from config import settings
from llm.base import LLMProvider, LLMResponse


class ClaudeProvider(LLMProvider):
    # Standardmodell: aktuell und akzeptiert weiterhin den temperature-Parameter,
    # der laut Forschungsdesign konstant niedrig gehalten wird. Neuere Modelle
    # (z.B. claude-opus-4-8) lehnen Sampling-Parameter ab -- dort temperature=None.
    def __init__(self, model_id: str = "claude-sonnet-4-6") -> None:
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY fehlt in .env")
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self._model_id = model_id

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def model_id(self) -> str:
        return self._model_id

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = 0.0,
        max_tokens: int = 8000,
    ) -> LLMResponse:
        kwargs = {
            "model": self._model_id,
            "max_tokens": max_tokens,
            "system": system or "",
            "messages": [{"role": "user", "content": prompt}],
        }
        if temperature is not None:
            kwargs["temperature"] = temperature

        start = time.perf_counter()
        response = self.client.messages.create(**kwargs)
        latency = time.perf_counter() - start

        text = "".join(b.text for b in response.content if b.type == "text")
        return LLMResponse(
            text=text,
            model=response.model,
            provider=self.provider_name,
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
            latency_seconds=latency,
            raw_response={"id": response.id, "stop_reason": response.stop_reason},
        )
