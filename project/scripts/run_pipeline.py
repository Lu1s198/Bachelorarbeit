"""Verkettete End-to-End-Pipeline (Code-Generierung) je Modell ausführen.

Jeder Schritt bekommt die Ausgabe des vorigen als Eingabe; nach jedem Schritt
werden Schema und abgeglichene Genauigkeit gegen die verkettete Referenz geprüft.
Bricht ein Schritt (Crash oder Schema-Bruch), werden abhängige Schritte blockiert.

Aufruf:
    python scripts/run_pipeline.py                        # alle 4 Modelle, Seed 1
    python scripts/run_pipeline.py --providers google
    python scripts/run_pipeline.py --providers anthropic openai --attempts 3
    python scripts/run_pipeline.py --seed 1
    python scripts/run_pipeline.py --providers baseline   # regelbasierte Vergleichsbasis
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "src"))

from experiments.pipeline_runner import run_all_pipelines  # noqa: E402

ALL_PROVIDERS = ["anthropic", "openai", "google", "ollama"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--providers", nargs="+", default=ALL_PROVIDERS,
                        help="anthropic openai google ollama baseline "
                             "(Standard: die vier Modelle)")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--attempts", type=int, default=3,
                        help="max. Code-Erzeugungs-Versuche je Schritt (Standard: 3)")
    args = parser.parse_args()

    results = run_all_pipelines(args.providers, seed=args.seed, attempts=args.attempts)

    print("\n" + "=" * 60)
    print("ZUSAMMENFASSUNG")
    for r in results:
        end = "Ende erreicht" if r["reached_end"] else "abgebrochen"
        print(f"  {r['provider']:10} {r['n_steps_ok']}/9 Schritte ok  ({end})")


if __name__ == "__main__":
    main()
