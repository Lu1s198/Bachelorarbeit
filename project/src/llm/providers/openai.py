"""OpenAI (GPT) Provider."""

import time

from openai import OpenAI, BadRequestError

from config import settings
from llm.base import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    # Neuere Modelle (GPT-5.x) verlangen max_completion_tokens statt max_tokens
    # und lehnen temperature != 1 ab; generate() faellt automatisch zurueck
    # (im Result als dropped_params protokolliert -- relevant fuer FF3).
    def __init__(self, model_id: str = "gpt-5.6-terra",
                 disable_thinking: bool = False) -> None:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY fehlt in .env")
        self.client = OpenAI(api_key=settings.openai_api_key)
        self._model_id = model_id
        self._disable_thinking = disable_thinking

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
            "max_completion_tokens": max_tokens,
        }
        if temperature is not None:
            kwargs["temperature"] = temperature
        # Hinweis: gpt-5.6-terra akzeptiert weder temperature=0 (Fallback unten
        # lässt ihn weg) noch reasoning_effort='minimal'. Ein explizites
        # Abschalten des Reasonings ist hier nicht möglich; disable_thinking
        # bleibt für OpenAI daher ohne zusätzlichen Parameter.

        start = time.perf_counter()
        dropped: list[str] = []
        try:
            response = self.client.chat.completions.create(**kwargs)
        except BadRequestError as exc:
            msg = str(exc)
            retriable = False
            for param in ("temperature", "reasoning_effort"):
                if param in msg and param in kwargs:
                    kwargs.pop(param)
                    dropped.append(param)
                    retriable = True
            if retriable:
                response = self.client.chat.completions.create(**kwargs)
            else:
                raise
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
                "dropped_params": dropped,
            },
        )
