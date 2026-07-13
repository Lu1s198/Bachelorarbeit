"""Google Gemini Provider."""

import time

import google.generativeai as genai

from config import settings
from llm.base import LLMProvider, LLMResponse


class GeminiProvider(LLMProvider):
    def __init__(self, model_id: str = "gemini-1.5-pro") -> None:
        if not settings.google_api_key:
            raise ValueError("GOOGLE_API_KEY fehlt in .env")
        genai.configure(api_key=settings.google_api_key)
        self._model_id = model_id

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
        gen_config: dict = {"max_output_tokens": max_tokens}
        if temperature is not None:
            gen_config["temperature"] = temperature

        model = genai.GenerativeModel(
            self._model_id,
            system_instruction=system or None,
            generation_config=gen_config,
        )

        start = time.perf_counter()
        response = model.generate_content(prompt)
        latency = time.perf_counter() - start

        usage = response.usage_metadata
        return LLMResponse(
            text=response.text,
            model=self._model_id,
            provider=self.provider_name,
            prompt_tokens=usage.prompt_token_count,
            completion_tokens=usage.candidates_token_count,
            latency_seconds=latency,
            raw_response={"finish_reason": str(response.candidates[0].finish_reason)},
        )
