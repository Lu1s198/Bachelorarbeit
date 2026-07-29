"""Ollama Provider (lokal ausführbares, offenes Modell, z.B. Llama)."""

import time

from ollama import Client

from config import settings
from llm.base import LLMProvider, LLMResponse


class OllamaProvider(LLMProvider):
    def __init__(self, model_id: str = "llama3.1") -> None:
        self.client = Client(host=settings.ollama_host)
        self._model_id = model_id

    @property
    def provider_name(self) -> str:
        return "ollama"

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

        options: dict = {"num_predict": max_tokens}
        if temperature is not None:
            options["temperature"] = temperature

        # Kontextfenster automatisch groß genug wählen (Default 4096 reicht nicht,
        # wenn -- wie im Direkt-Modus -- die Rohdaten mit ins Prompt eingebettet
        # werden). Grob: Eingabe- + Ausgabe-Tokens, auf 2er-Potenz aufgerundet.
        approx_in = (len(prompt) + len(system or "")) // 4
        ctx = 4096
        while ctx < approx_in + max_tokens + 512:
            ctx *= 2
        # Cap bei 8192: größere KV-Caches sprengen auf 8-GB-GPUs das VRAM und
        # fallen extrem langsam auf die CPU zurück. Im Direkt-Modus wird die
        # Ausgabe dadurch ggf. abgeschnitten (schneller Fehlschlag statt Hänger).
        options["num_ctx"] = min(ctx, 8192)

        start = time.perf_counter()
        response = self.client.chat(
            model=self._model_id, messages=messages, options=options
        )
        latency = time.perf_counter() - start

        return LLMResponse(
            text=response["message"]["content"],
            model=response.get("model", self._model_id),
            provider=self.provider_name,
            prompt_tokens=response.get("prompt_eval_count", 0),
            completion_tokens=response.get("eval_count", 0),
            latency_seconds=latency,
            raw_response={"done_reason": response.get("done_reason", "")},
        )
