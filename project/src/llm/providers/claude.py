"""Anthropic Claude Provider."""

import time

from anthropic import Anthropic, BadRequestError

from config import settings
from llm.base import LLMProvider, LLMResponse


class ClaudeProvider(LLMProvider):
    # Neuere Modelle (Sonnet 5, Opus 4.x) lehnen den temperature-Parameter ab;
    # generate() faellt in dem Fall automatisch darauf zurueck, ihn wegzulassen
    # (im Result als dropped_params protokolliert -- relevant fuer FF3).
    def __init__(self, model_id: str = "claude-sonnet-5",
                 disable_thinking: bool = False) -> None:
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY fehlt in .env")
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self._model_id = model_id
        self._disable_thinking = disable_thinking

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def model_id(self) -> str:
        return self._model_id

    def _create(self, kwargs: dict):
        """Streaming-Aufruf: nötig bei großem max_tokens (Anthropic verlangt
        Streaming für potenziell >10-minütige Anfragen, z.B. im Direkt-Modus)."""
        with self.client.messages.stream(**kwargs) as stream:
            stream.until_done()
            return stream.get_final_message()

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
        if self._disable_thinking:
            kwargs["thinking"] = {"type": "disabled"}

        start = time.perf_counter()
        dropped: list[str] = []
        try:
            response = self._create(kwargs)
        except BadRequestError as exc:
            if "temperature" in str(exc) and "temperature" in kwargs:
                kwargs.pop("temperature")
                dropped.append("temperature")
                response = self._create(kwargs)
            else:
                raise
        latency = time.perf_counter() - start

        text = "".join(b.text for b in response.content if b.type == "text")
        return LLMResponse(
            text=text,
            model=response.model,
            provider=self.provider_name,
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
            latency_seconds=latency,
            raw_response={"id": response.id, "stop_reason": response.stop_reason,
                          "dropped_params": dropped},
        )
