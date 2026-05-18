# KI-unterstützte Erstellung von ETL-Prozessen — Experimenteller Code

Praktischer Teil der Bachelorarbeit. Dieses Repo enthält:

- Generator für den **synthetischen Datensatz**
- Einheitliches **Provider-Interface** für Claude, GPT, Gemini, Ollama
- **Experiment-Runner** über die Matrix `Modell × Prompt × Aufgabe`
- **Evaluation** nach Korrektheit, Code-Qualität, Performance, Robustheit
- **Notebooks** zur Auswertung und für die Abbildungen der Arbeit

## Schnellstart

```bash
# 1. uv installieren (einmalig, ersetzt pip+venv+pyenv)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Dependencies installieren (erzeugt .venv automatisch)
uv sync

# 3. .env aus Template erzeugen und API-Keys eintragen
cp .env.example .env
# -> editiere .env

# 4. Tests laufen lassen
uv run pytest

# 5. (Beispiel) Datensatz generieren
uv run python scripts/generate_dataset.py
```

## Reproduzierbarkeit

Folgende Mechanismen sichern die wissenschaftliche Reproduzierbarkeit:

1. **`uv.lock`** — exakte Versionen aller (auch transitive) Dependencies.
   Wird beim ersten `uv sync` erzeugt und **muss** committet werden.
2. **`.python-version`** — pinnt Python 3.12.
3. **Globaler Seed** in `.env` (`RANDOM_SEED=42`) — wird in allen Generatoren
   verwendet. Gleicher Seed → identischer Datensatz.
4. **Modell-Versionen** werden in jedem Ergebnis-JSON mitgeloggt
   (Provider liefert `model` zurück, nicht nur den Alias).
5. **Prompts versioniert** in `prompts/` (v1, v2, …) — alte Versionen
   bleiben erhalten.
6. **Ergebnis-JSONs** enthalten Timestamp, Modell-ID, Prompt-ID, Seed,
   Roh-Output. Nichts wird überschrieben.

## Projektstruktur

```
src/ba_ki_etl/          Hauptcode (Provider, Generator, Eval, Runner)
prompts/                Versionierte Prompt-Vorlagen (YAML)
data/synthetic/         Generierte Datensätze (per Seed reproduzierbar)
data/ground_truth/      Erwartete Ergebnisse pro Aufgabe
data/results/           Roh-Outputs der Experimente
notebooks/              Auswertung und Abbildungen
tests/                  pytest
scripts/                Einstiegspunkte (CLI)
```

## Workflow für die Arbeit

1. **Datensatz designen** → `dataset/scenarios.py` (welche ETL-Probleme?)
2. **Datensatz generieren** → `scripts/generate_dataset.py`
3. **Ground Truth** für jede Aufgabe einmalig per Hand erzeugen und committen
4. **Prompts entwerfen** → `prompts/v*.yaml`
5. **Experimente laufen lassen** → `scripts/run_experiments.py`
6. **Auswerten** → `notebooks/02_results_analysis.ipynb`
7. **Plots für die Arbeit** → `notebooks/03_figures_for_thesis.ipynb`,
   per `matplotlib.savefig()` als PDF in den LaTeX-Ordner exportieren.

## Anbindung an die LaTeX-Arbeit

Empfohlen: die generierten Abbildungen direkt aus `notebooks/03_*.ipynb`
als PDF in den `figures/`-Ordner deines LaTeX-Projekts speichern. Bei
Updates des Datensatzes oder neuer Experimente reicht ein Notebook-Rerun,
um alle Abbildungen zu aktualisieren.

## Was noch zu tun ist (TODOs)

Dieses Repo ist das **Grundgerüst**. Konkret offen:

- [ ] Datensatz-Szenarien designen (welche ETL-Schwierigkeiten?)
- [ ] Ground Truth für jede Aufgabe erzeugen
- [ ] Weitere Provider implementieren (OpenAI, Gemini, Ollama)
- [ ] Experiment-Runner ausbauen (Matrix-Iteration, Result-Logging)
- [ ] Weitere Eval-Module: `code_quality.py`, `performance.py`, `robustness.py`
- [ ] Prompts v2–v4 erstellen (Few-Shot, CoT, mit Schema)
- [ ] Notebook-Vorlagen für die Auswertung
```
