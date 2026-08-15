"""Verkettete Pipeline im Direkt-Modus (Daten im Prompt statt generiertem Code).

Gegenstueck zu ``run_pipeline.py``. Der Modus ist durch das Ausgabefenster
begrenzt und daher fuer den halbierten Datensatz gedacht:

    python scripts/make_half_dataset.py            # erzeugt Seed 101
    python scripts/run_pipeline_direct.py --seed 101

Weitere Aufrufe:
    python scripts/run_pipeline_direct.py --seed 101 --providers anthropic
    python scripts/run_pipeline_direct.py --seed 101 --inputs reference
    python scripts/run_pipeline_direct.py --seed 101 --estimate-only
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "src"))

from config import settings  # noqa: E402
from experiments.pipeline_direct import (  # noqa: E402
    DEFAULT_MAX_TOKENS, run_all_pipelines_direct,
)
from experiments.pipeline_runner import PIPELINE, build_chain_reference  # noqa: E402

ALL_PROVIDERS = ["anthropic", "openai", "google", "ollama"]

# Empirisch aus den tatsaechlichen Laeufen bestimmt: Zeichen der erzeugten
# Antwort geteilt durch die abgerechneten completion_tokens, und zwar als
# *schlechtester* beobachteter Wert je Modell. Der Faktor haengt sowohl vom
# Modell als auch vom Inhalt ab -- Gemini schaffte 2,0 Zeichen/Token bei der
# textlastigen Kundentabelle, aber nur 1,0 bei der zahlenlastigen Bestelltabelle,
# wo jede Zifferngruppe ein eigenes Token wird. Eine Schaetzung mit einem
# gemeinsamen Faktor hat den Abbruch bei Gemini genau deshalb nicht vorhergesagt.
ZEICHEN_PRO_TOKEN = {"anthropic": 1.55, "openai": 1.50, "google": 1.00, "ollama": 1.30}


def schaetzung(seed: int, max_tokens: int, providers: list[str]) -> bool:
    """Gibt den Token-Bedarf je Schritt aus. True, wenn alles ins Budget passt.

    Bewertet je Modell, weil sich die Token-Effizienz erheblich unterscheidet."""
    ref = build_chain_reference(seed)
    d = settings.synthetic_dir / str(seed)
    roh = {f"raw:{f}": pd.read_csv(d / f, dtype=str)
           for f in ["customers_raw.csv", "products_raw.csv", "orders_raw.csv"]}
    zeichen = {s.name: len(ref[s.name].to_csv(index=False)) for s in PIPELINE}
    relevant = [p for p in providers if p in ZEICHEN_PRO_TOKEN]

    print(f"Token-Schaetzung fuer Seed {seed} (Budget je Antwort: {max_tokens})")
    kopf = "".join(f"{p[:6]:>9}" for p in relevant)
    print(f"  {'Schritt':16} {'Eingabe':>9}  Ausgabe je Modell:{kopf}")
    passt = True
    for step in PIPELINE:
        ein = sum(len((roh[s] if s.startswith("raw:") else ref[s.split(":", 1)[1]])
                      .to_csv(index=False)) / 1.96 for _, s in step.inputs)
        zeile, warnung = "", ""
        for p in relevant:
            aus = round(zeichen[step.name] / ZEICHEN_PRO_TOKEN[p])
            zeile += f"{aus:9}"
            if aus > max_tokens:
                passt = False
                warnung = "   ACHTUNG"
            elif aus > max_tokens * 0.6 and not warnung:
                warnung = "   knapp"
        print(f"  {step.name:16} {round(ein):9}  {'':18}{zeile}{warnung}")
    print("\n  Angegeben ist der Bedarf fuer die Tabelle allein. Reasoning-Modelle "
          "verbuchen ihre\n  verborgenen Denk-Token ebenfalls als completion_tokens "
          "und zehren am selben Budget\n  (bei Gemini im Endschritt rund 31.000). "
          "Deshalb gilt bereits ab 60 % als knapp.")
    if not passt:
        print("\n  Mindestens ein Modell sprengt bei mindestens einem Schritt das "
              "Ausgabebudget.\n  Abhilfe: hoeheres --max-tokens oder kleinerer "
              "Datensatz (scripts/make_half_dataset.py).")
    return passt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--providers", nargs="+", default=ALL_PROVIDERS)
    parser.add_argument("--seed", type=int, default=101)
    parser.add_argument("--rep", type=int, default=1,
                        help="Nummer der Wiederholung. 1 schreibt in den "
                             "schlichten Ordner, ab 2 in <modell>..._r<N>, sodass "
                             "sich Wiederholungen nicht ueberschreiben")
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS,
                        dest="max_tokens", help="Ausgabebudget je Schritt")
    parser.add_argument("--inputs", choices=["self", "reference"], default="self",
                        dest="input_source",
                        help="'self': verkettet. 'reference': jeder Schritt erhaelt "
                             "die Soll-Ausgabe des Vorgaengers (Ergebnisse in "
                             "<provider>_direct_isolated/)")
    parser.add_argument("--estimate-only", action="store_true", dest="estimate_only",
                        help="nur den Token-Bedarf ausgeben, nichts ausfuehren")
    parser.add_argument("--force", action="store_true",
                        help="auch starten, wenn die Schaetzung das Budget sprengt")
    args = parser.parse_args()

    passt = schaetzung(args.seed, args.max_tokens, args.providers)
    if args.estimate_only:
        return
    if not passt and not args.force:
        print("\nAbgebrochen. Mit --force trotzdem ausfuehren.")
        sys.exit(1)
    print()

    results = run_all_pipelines_direct(
        args.providers, seed=args.seed, attempts=args.attempts,
        input_source=args.input_source, max_tokens=args.max_tokens,
        rep=args.rep)

    print("\n" + "=" * 60)
    print("ZUSAMMENFASSUNG")
    for r in results:
        ende = "Ende erreicht" if r["reached_end"] else "abgebrochen"
        abgeschnitten = sum(1 for s in r["steps"] if s.get("truncated"))
        hinweis = f", {abgeschnitten} abgeschnitten" if abgeschnitten else ""
        print(f"  {r['provider']:10} {r['n_steps_ok']}/9 Schritte ok  ({ende}{hinweis})")


if __name__ == "__main__":
    main()
