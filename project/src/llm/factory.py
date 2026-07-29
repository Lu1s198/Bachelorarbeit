"""Factory für die austauschbare Provider-Instanziierung.

Erlaubt es dem Experiment-Runner, Modelle allein über einen Namen anzusprechen
und so den Versuchsablauf unabhängig vom konkreten Anbieter zu halten.
"""

from __future__ import annotations

from llm.base import LLMProvider

# Ein repräsentativer Vertreter je Anbieter (Kapitel 4.2). Anpassen an die
# tatsächlich verfügbaren Modelle. temperature=None hinterlegen, falls ein
# Modell keine Sampling-Parameter akzeptiert.
DEFAULT_MODELS: dict[str, str] = {
    "anthropic": "claude-sonnet-5",
    "openai": "gpt-5.6-terra",
    "google": "gemini-3.6-flash",
    "ollama": "llama3.1",
}

_ALIASES = {
    "claude": "anthropic",
    "gpt": "openai",
    "gemini": "google",
    "llama": "ollama",
}


def get_provider(name: str, model: str | None = None,
                 disable_thinking: bool = False) -> LLMProvider:
    """Liefert eine Provider-Instanz für 'anthropic' | 'openai' | 'google' | 'ollama'.

    Die Provider (und damit ihre SDKs) werden erst hier importiert, sodass ein
    fehlendes SDK nur dann stört, wenn der betreffende Anbieter genutzt wird.

    disable_thinking schaltet das (bei aktuellen Modellen standardmäßige)
    Reasoning ab -- nötig für den Direkt-Modus, wo das Denken sonst das
    Output-Budget für die Ergebnistabelle aufbraucht. Ollama (llama3.1) denkt
    ohnehin nicht.
    """
    key = _ALIASES.get(name.lower(), name.lower())
    if key not in DEFAULT_MODELS:
        raise KeyError(f"Unbekannter Provider: {name}")
    model_id = model or DEFAULT_MODELS[key]

    if key == "anthropic":
        from llm.providers.claude import ClaudeProvider
        return ClaudeProvider(model_id=model_id, disable_thinking=disable_thinking)
    if key == "openai":
        from llm.providers.openai import OpenAIProvider
        return OpenAIProvider(model_id=model_id, disable_thinking=disable_thinking)
    if key == "google":
        from llm.providers.gemini import GeminiProvider
        return GeminiProvider(model_id=model_id, disable_thinking=disable_thinking)
    from llm.providers.ollama import OllamaProvider
    return OllamaProvider(model_id=model_id)
