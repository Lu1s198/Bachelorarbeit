# KI-unterstützte Erstellung von ETL-Prozessen — Experimenteller Code

Praktischer Teil der Bachelorarbeit. Dieses Repo setzt das in den Kapiteln 4–7
beschriebene Untersuchungsdesign um:

- **Synthetischer Datensatz** mit bekannter Ground Truth (Kapitel 5)
- **Referenzlösungen** = Soll-Lösung jeder der neun ETL-Aufgaben
- **Klassische, regelbasierte Pipeline** als Vergleichsbasis (Kapitel 4.6)
- **Einheitliches Provider-Interface** für Claude, GPT, Gemini, Ollama (Kapitel 4.2)
- **Code-Generierungs-Ansatz**: das LLM erzeugt ein pandas-Skript, das
  deterministisch ausgeführt und gegen die Ground Truth bewertet wird (Kapitel 4.1)
- **Experiment-Runner** über die Matrix `Modell × Prompt-Strategie × Aufgabe`
- **Evaluation** nach Genauigkeit, Vollständigkeit, Konsistenz, Effizienz (Kapitel 4.5)

## Schnellstart

```bash
# 1. uv installieren (einmalig; ersetzt pip+venv). Siehe https://astral.sh/uv
#    Danach Dependencies installieren (erzeugt .venv + uv.lock):
uv sync

# 2. API-Keys eintragen
cp .env.example .env      # dann .env editieren (nur die Anbieter, die du nutzt)

# 3. Datensatz + Ground Truth erzeugen (deterministisch je Seed)
uv run python scripts/generate_datasets.py --seed 1

# 4. Klassische Vergleichsbasis rechnen (ohne API-Keys)
uv run python scripts/run_baseline.py --seed 1

# 5. Schneller LLM-Testlauf (nur ein Anbieter/Prompt/Aufgabe, 1 Wiederholung)
uv run python scripts/run_experiments.py \
    --providers anthropic --prompts v1_zero_shot \
    --tasks cleaning_easy_missing_and_whitespace --repetitions 1

# 6. Vollständige Matrix (alle Anbieter mit Key × alle Prompts × alle Aufgaben)
uv run python scripts/run_experiments.py --seed 1 --repetitions 3

# Tests
uv run pytest
```

> Ohne uv geht es auch mit venv+pip: `python -m venv .venv`, aktivieren,
> `pip install pandas pyarrow faker pyyaml anthropic openai google-generativeai ollama pydantic pydantic-settings python-dotenv pytest`.

## Ablauf der Auswertung

Jeder Lauf schreibt genau ein Ergebnis-JSON nach
`data/results/<seed>/<task>/…json` mit Zeitstempel, Modell-ID, Prompt-ID, Seed,
Wiederholung, Token-/Kosten-/Zeitkennzahlen, dem **erzeugten Code** und den
Korrektheitsmetriken. Nichts wird überschrieben — die JSONs sind die Datenbasis
für die Notebooks (`notebooks/`), aus denen die Abbildungen der Arbeit entstehen.

## Projektstruktur

```
src/
  config.py              zentrale Settings (.env, Seeds, Temperatur, Wiederholungen)
  dataset/
    schemas.py           Zielschemata + Varianten-Tabelle (Ländernamen)
    scenarios.py         Definition der neun Aufgaben (3 Kategorien × 3 Stufen)
    generator.py         zweistufige Erzeugung: sauber -> kontrolliert verfälscht
    reference.py         Referenzlösungen = Ground Truth je Aufgabe
  baseline/pipeline.py   klassische, regelbasierte ETL-Pipeline (Vergleichsbasis)
  llm/
    base.py              LLMProvider-Interface + LLMResponse
    providers/           claude / openai / gemini / ollama (lazy geladen)
    factory.py           get_provider("anthropic" | "openai" | ...)
    prompt.py            Laden/Rendern der Prompt-Vorlagen
    pricing.py           grobe Kostenschätzung je Modell
  evaluation/correctness.py   Genauigkeit / Vollständigkeit / Konsistenz
  experiments/
    code_execution.py    Code aus Antwort extrahieren + im Subprozess ausführen
    runner.py            Matrix-Iteration + Ergebnis-Logging
prompts/                 versionierte Strategien: v1 zero-shot … v4 schema
data/synthetic/<seed>/   Rohdaten (per Seed reproduzierbar)
data/ground_truth/<seed>/ saubere Referenz + Soll-Lösung je Aufgabe (Parquet)
data/results/<seed>/     Ergebnis-JSONs der Läufe
scripts/                 CLI-Einstiegspunkte
tests/                   pytest
```

## Reproduzierbarkeit

1. `uv.lock` — exakte Versionen aller Dependencies (beim ersten `uv sync`
   erzeugt, **committen**).
2. `.python-version` — pinnt Python 3.12.
3. **Seed** steuert Generierung *und* Verfälschung → gleicher Seed = bit-identischer
   Datensatz und identische Ground Truth.
4. **Temperatur** konstant niedrig (`--temperature 0.0`, Default) über alle Läufe.
5. **Modell-Version** wird pro Ergebnis-JSON mitgeloggt (`response.model`).
6. **Prompts versioniert** in `prompts/` (v1…v4).

## Hinweise / bewusste Entscheidungen

- **Ground Truth vs. Baseline**: Die Referenzlösungen (`dataset/reference.py`)
  nutzen privilegiertes Wissen aus der Generierung (Inverse der Varianten-Tabelle,
  ID-Grenze der Originale, saubere Tabellen) und bilden die *korrekte* Soll-Lösung.
  Die klassische Pipeline (`baseline/pipeline.py`) sieht dieses Wissen **nicht**
  und arbeitet mit realistischen Regeln — deshalb erreicht sie bei den
  formalisierbaren Aufgaben 100 %, verliert aber bei semantischer
  Länder-Vereinheitlichung und Fuzzy-Duplikaten (Hypothese H1).
- **Reihenfolge-unabhängige Bewertung**: Vor dem zellweisen Abgleich werden
  Ist- und Soll-Tabelle nach allen Spalten sortiert (LLM-Code liefert korrekte
  Ergebnisse oft in anderer Zeilenreihenfolge). Weicht die Struktur (Spalten,
  Datensatzanzahl) ab, wird das über `comparable=false` gesondert ausgewiesen.
- **Sicherheit**: Der Runner führt vom Modell erzeugten Code in einem separaten
  Prozess mit Timeout aus. Das ist für die kontrollierte, lokale Durchführung
  vertretbar — nicht auf Produktivsystemen einsetzen.
- **Neueste Claude-Modelle** (z.B. `claude-opus-4-8`) lehnen den
  `temperature`-Parameter ab. Default ist daher `claude-sonnet-4-6` (aktuell und
  temperaturfähig). Für Modelle ohne Sampling-Parameter im Runner `temperature`
  weglassen (in `run_single`/`run_experiments` auf `None` setzen).

## Offene TODOs (für dich)

- [ ] `uv sync` + `.env` mit deinen API-Keys füllen
- [ ] Repräsentative Modelle je Anbieter in `llm/factory.py` (`DEFAULT_MODELS`)
      final festlegen (Aktualität dokumentieren, Kapitel 4.2)
- [ ] Ollama lokal installieren + Modell ziehen (`ollama pull llama3.1`)
- [ ] Ergebnis-Notebooks bauen: Aggregation der JSONs + Abbildungen als PDF in
      den LaTeX-`figures/`-Ordner exportieren
- [ ] Optional: Code-Qualitäts-Metriken (radon) als eigenes Eval-Modul ergänzen
```
