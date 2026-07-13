"""Grobe Kostenschätzung je Modell für das Effizienzkriterium (Kapitel 4.5.4).

Preise in USD pro 1 Mio. Tokens (Input, Output). Bei Bedarf an die aktuellen
Listenpreise anpassen; lokale Modelle (Ollama) verursachen keine Modellkosten.
"""

from __future__ import annotations

# (input_per_1M, output_per_1M)
PRICES: dict[str, tuple[float, float]] = {
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-opus-4-8": (5.00, 25.00),
    "gpt-4o": (2.50, 10.00),
    "gemini-1.5-pro": (1.25, 5.00),
    "llama3.1": (0.0, 0.0),
}


def estimate_cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float | None:
    """Schätzt die Kosten eines Aufrufs. None, wenn kein Preis hinterlegt ist."""
    for key, (pin, pout) in PRICES.items():
        if model.startswith(key):
            return round(prompt_tokens / 1e6 * pin + completion_tokens / 1e6 * pout, 6)
    return None
