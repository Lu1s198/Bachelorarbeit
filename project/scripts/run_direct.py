"""Führt die Experimente im Direkt-Modus aus (Daten ins Prompt, CSV zurück).

Nur EIN Lauf je (Modell x Aufgabe); Retry nur bei technischem Fehlschlag.

Beispiele:
    # Alles (4 Provider x 9 Aufgaben):
    python scripts/run_direct.py

    # Nur die semantischen Aufgaben, ein Provider:
    python scripts/run_direct.py --providers anthropic \
        --tasks cleaning_hard_semantic_unification dedup_hard_fuzzy_duplicates
"""

import argparse
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "src"))

from dataset.scenarios import ALL_TASKS  # noqa: E402
from experiments.direct_runner import run_direct_experiments  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--providers", nargs="+",
                        default=["anthropic", "openai", "google", "ollama"])
    parser.add_argument("--tasks", nargs="+", default=None, help="Default: alle neun")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--max-tokens", type=int, default=32000,
                        help="Output-Limit (angehoben, da die Ergebnistabelle zurückkommt)")
    parser.add_argument("--attempts", type=int, default=3,
                        help="Max. Versuche bei technischem Fehlschlag (API/leere Antwort)")
    args = parser.parse_args()

    task_ids = args.tasks or [t.id for t in ALL_TASKS]
    results = run_direct_experiments(
        providers=args.providers, task_ids=task_ids, seed=args.seed,
        max_tokens=args.max_tokens, attempts=args.attempts)
    ok = sum(1 for r in results if (r.get("correctness") or {}).get("comparable"))
    print(f"\nFertig: {len(results)} Läufe, davon {ok} auswertbar.")


if __name__ == "__main__":
    main()
