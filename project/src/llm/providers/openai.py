"""OpenAI (GPT) Provider."""

import time

from openai import OpenAI

from config import settings
from llm.base import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    def __init__(self, model_id: str = "gpt-4o") -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY fehlt in .env")
        self.client = OpenAI(api_key=settings.openai_api_key)
        self._model_id = model_id

    @property
    def provider_name(self) -> str:
        return "openai"

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
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        kwargs = {
            "model": self._model_id,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        if temperature is not None:
            kwargs["temperature"] = temperature

        start = time.perf_counter()
        response = self.client.chat.completions.create(**kwargs)
        latency = time.perf_counter() - start

        return LLMResponse(
            text=response.choices[0].message.content or "",
            model=response.model,
            provider=self.provider_name,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            latency_seconds=latency,
            raw_response={
                "id": response.id,
                "finish_reason": response.choices[0].finish_reason,
            },
        )
