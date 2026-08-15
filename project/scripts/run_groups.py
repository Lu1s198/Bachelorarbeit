"""Prompting-Strategien auf gedrittelter Strecke.

Die neun Pipeline-Schritte werden zu drei Gruppen zusammengefasst (1-3, 4-6,
7-9); jede Gruppe bekommt die Soll-Ausgabe ihrer Vorgaengergruppe. Damit bleibt
die Komposition mehrerer Schritte als Anforderung erhalten, ohne dass ein Fehler
aus einer frueheren Gruppe den Strategievergleich ueberdeckt.

Aufrufe:
    python scripts/run_groups.py --seed 2
    python scripts/run_groups.py --seed 2 --groups transform
    python scripts/run_groups.py --seed 2 --providers anthropic --repetition 2
"""

import argparse
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "src"))

from experiments.group_runner import GROUPS, run_all_groups  # noqa: E402

CLASSIC = ["v1_zero_shot", "v2_few_shot", "v3_chain_of_thought"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--providers", nargs="+",
                        default=["anthropic", "openai", "google"])
    parser.add_argument("--prompts", nargs="+", default=CLASSIC)
    parser.add_argument("--groups", nargs="+", default=None,
                        choices=[g.name for g in GROUPS],
                        help="Default: alle drei Gruppen")
    parser.add_argument("--seed", type=int, default=2)
    parser.add_argument("--repetition", type=int, default=1,
                        help="Nummer der Wiederholung. 1 schreibt in den "
                             "schlichten Ordner, ab 2 in <lauf>_r<N>")
    parser.add_argument("--attempts", type=int, default=3)
    args = parser.parse_args()

    n = (len(args.providers) * len(args.prompts)
         * (len(args.groups) if args.groups else len(GROUPS)))
    print(f"{n} Laeufe: {len(args.providers)} Modelle x {len(args.prompts)} "
          f"Strategien x {len(args.groups) if args.groups else len(GROUPS)} Gruppen\n")

    ergebnisse = run_all_groups(args.providers, args.prompts, args.seed,
                                attempts=args.attempts, repetition=args.repetition,
                                groups=args.groups)

    print("\n" + "=" * 62)
    print("ZUSAMMENFASSUNG")
    ok = [r for r in ergebnisse if r["status"] == "ok"]
    kosten = sum(r["cost_usd"] for r in ergebnisse)
    dauer = sum(r["duration_s"] for r in ergebnisse)
    print(f"  {len(ok)}/{len(ergebnisse)} Laeufe verwertbar, "
          f"${kosten:.2f}, {dauer / 60:.1f} min")
    for g in GROUPS:
        teil = [r for r in ergebnisse if r["group"] == g.name]
        if not teil:
            continue
        mittel = sum(r["accuracy"] or 0.0 for r in teil) / len(teil)
        print(f"  {g.label:44} Ø {mittel:.3f}")


if __name__ == "__main__":
    main()
