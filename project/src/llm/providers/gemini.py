"""Google Gemini Provider (neues google-genai SDK)."""

import time

from google import genai
from google.genai import types

from config import settings
from llm.base import LLMProvider, LLMResponse


class GeminiProvider(LLMProvider):
    def __init__(self, model_id: str = "gemini-3.6-flash",
                 disable_thinking: bool = False) -> None:
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY fehlt in .env")
        self._client = genai.Client(api_key=settings.google_api_key)
        self._model_id = model_id
        self._disable_thinking = disable_thinking

    @property
    def provider_name(self) -> str:
        return "google"

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
        config = types.GenerateContentConfig(
            system_instruction=system or None,
            temperature=temperature,
            max_output_tokens=max_tokens,
            # gemini-3.6-flash lässt budget=0 nicht zu; 128 ist das Minimum, das
            # akzeptiert wird und das Denken praktisch ausschaltet.
            thinking_config=(types.ThinkingConfig(thinking_budget=128)
                             if self._disable_thinking else None),
        )

        start = time.perf_counter()
        response = self._client.models.generate_content(
            model=self._model_id, contents=prompt, config=config
        )
        latency = time.perf_counter() - start

        usage = response.usage_metadata
        # Gemini 3.x sind Reasoning-Modelle: die Denk-Tokens werden separat als
        # thoughts_token_count gezaehlt, aber zum Output-Tarif abgerechnet. Fuer
        # eine korrekte Kostenschaetzung (Kapitel 4.5.4) muessen sie in die
        # completion_tokens einfliessen.
        candidate_tokens = usage.candidates_token_count or 0
        thinking_tokens = usage.thoughts_token_count or 0

        finish_reason = (
            str(response.candidates[0].finish_reason) if response.candidates else None
        )

        return LLMResponse(
            text=response.text or "",
            model=self._model_id,
            provider=self.provider_name,
            prompt_tokens=usage.prompt_token_count or 0,
            completion_tokens=candidate_tokens + thinking_tokens,
            latency_seconds=latency,
            raw_response={
                "finish_reason": finish_reason,
                "candidate_tokens": candidate_tokens,
                "thinking_tokens": thinking_tokens,
            },
        )
