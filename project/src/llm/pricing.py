"""Grobe Kostenschätzung je Modell für das Effizienzkriterium (Kapitel 4.5.4).

Preise in USD pro 1 Mio. Tokens (Input, Output), Listenpreise der Anbieter.
Reasoning-/Thinking-Tokens werden von allen drei Anbietern zum Output-Tarif
abgerechnet und sind in den Providern bereits in den completion_tokens
enthalten. Lokale Modelle (Ollama) verursachen keine Modellkosten.

Stand der Preise: abgerufen am 2026-07-27 von den Anbieter-Preisseiten.
Vor dem finalen Lauf gegenchecken -- Modellnamen und Preise ändern sich schnell.
"""

from __future__ import annotations

# (input_per_1M, output_per_1M)
PRICES: dict[str, tuple[float, float]] = {
    # --- Anthropic (Claude) ---
    # Sonnet 5: Listenpreis 3.00/15.00; Einführungspreis 2.00/10.00 noch bis
    # 2026-08-31. Hier bewusst der stabile Listenpreis (konservativ, zitierbar).
    "claude-sonnet-5": (3.00, 15.00),
    "claude-opus-4-8": (5.00, 25.00),
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-sonnet-4-6": (3.00, 15.00),  # Vorgänger, falls noch referenziert
    # --- OpenAI (GPT) ---
    "gpt-5.6-sol": (5.00, 30.00),
    "gpt-5.6-terra": (2.50, 15.00),
    "gpt-5.6-luna": (1.00, 6.00),
    # --- Google (Gemini) ---
    "gemini-3.6-flash": (1.50, 7.50),
    "gemini-3.1-pro": (2.00, 12.00),      # deckt auch -preview ab (startswith)
    "gemini-3.1-flash-lite": (0.10, 0.40),
    # --- Lokal ---
    "llama3.1": (0.0, 0.0),
}


def estimate_cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float | None:
    """Schätzt die Kosten eines Aufrufs. None, wenn kein Preis hinterlegt ist.

    Zuordnung per Prefix; bei Überschneidungen gewinnt der längste (spezifischste)
    Schlüssel, damit z.B. 'gpt-5.6-terra' nicht versehentlich auf ein kürzeres
    'gpt-5.6' matcht.
    """
    for key in sorted(PRICES, key=len, reverse=True):
        if model.startswith(key):
            pin, pout = PRICES[key]
            return round(prompt_tokens / 1e6 * pin + completion_tokens / 1e6 * pout, 6)
    return None
