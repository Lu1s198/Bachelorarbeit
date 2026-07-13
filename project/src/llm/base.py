"""Abstrakte Basis für alle LLM-Provider.

Jeder Provider (Claude, GPT, Gemini, Ollama) implementiert dieses Interface,
sodass der Experiment-Runner austauschbar mit allen Modellen arbeitet
(einheitliche Schnittstelle, Kapitel 4.2 / Abschnitt sec:llm-integration).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMResponse:
    """Standardisierte Antwort eines LLM-Aufrufs.

    Alle Felder werden im Result-JSON mitgeloggt -- das ist die Datenbasis
    für die spätere Auswertung in der Arbeit.
    """

    text: str
    model: str           # exakter Modell-Identifier, z.B. "claude-sonnet-4-6"
    provider: str        # "anthropic", "openai", "google", "ollama"
    prompt_tokens: int
    completion_tokens: int
    latency_seconds: float
    raw_response: dict    # gekürzte API-Antwort für nachträgliche Analysen


class LLMProvider(ABC):
    """Gemeinsames Interface für alle Modell-Anbieter."""

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def model_id(self) -> str: ...

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = 0.0,
        max_tokens: int = 8000,
    ) -> LLMResponse:
        """Erzeugt eine Antwort auf den gegebenen Prompt.

        temperature=None weist den Provider an, den Parameter wegzulassen
        (nötig für neuere Modelle, die keine Sampling-Parameter akzeptieren).
        """
        ...
