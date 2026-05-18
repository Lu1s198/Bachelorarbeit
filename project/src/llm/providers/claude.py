"""Anthropic Claude Provider."""

import time

from anthropic import Anthropic

from project.src.config import settings
from project.src.llm.base import LLMProvider, LLMResponse


class ClaudeProvider(LLMProvider):
    def __init__(self, model_id: str = "claude-opus-4-5") -> None:
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
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        start = time.perf_counter()
        response = self.client.messages.create(
            model=self._model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system or "",
            messages=[{"role": "user", "content": prompt}],
        )
        latency = time.perf_counter() - start

        # Text aus allen Text-Blöcken extrahieren
        text = "".join(block.text for block in response.content if block.type == "text")

        return LLMResponse(
            text=text,
            model=response.model,
            provider=self.provider_name,
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
            latency_seconds=latency,
            raw_response=response.model_dump(),
        )
