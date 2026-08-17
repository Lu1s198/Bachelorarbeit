"""Zusammengesetzte Aufgabe mit explizit aufgezaehlten Teilschritten.

Trennt zwei Erklaerungen fuer das Scheitern der Aufgabe
``transform_hard_join_and_aggregate``: unzureichende Kompositionsfaehigkeit der
Modelle oder eine unausgesprochene Anforderung in der Aufgabenstellung. Gestellt
wird dieselbe Verarbeitung, jedoch mit benannten Teilschritten, in beiden
Ausfuehrungsmodi und unter allen drei Prompting-Strategien.

Aufrufe:
    python scripts/run_composite.py --seed 2                  # beide Modi
    python scripts/run_composite.py --seed 2 --modes codegen  # nur Code-Gen
    python scripts/run_composite.py --seed 2 --estimate-only
"""

import argparse
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "src"))

from experiments.composite_runner import (  # noqa: E402
    CODEGEN_PROMPTS, DIRECT_PROMPTS, build_reference, run_all_composite,
)

# Mittlere Kosten je Lauf, empirisch aus den bisherigen Laeufen derselben
# Aufgabe: Der Direkt-Modus fuehrt alle drei Rohtabellen im Prompt mit.
KOSTEN = {"codegen": 0.031, "direct": 0.163}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--providers", nargs="+",
                        default=["anthropic", "openai", "google"])
    parser.add_argument("--modes", nargs="+", default=["codegen", "direct"],
                        choices=["codegen", "direct"])
    parser.add_argument("--seed", type=int, default=2)
    parser.add_argument("--rep", type=int, default=1)
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--max-tokens", type=int, default=None, dest="max_tokens")
    parser.add_argument("--estimate-only", action="store_true",
                        dest="estimate_only")
    args = parser.parse_args()

    soll = build_reference(args.seed)
    print(f"Soll-Loesung (Seed {args.seed}): {len(soll)} Zeilen, "
          f"{soll.country_code.nunique()} Laendercodes, "
          f"{int(soll.order_count.sum())} Bestellungen erfasst")

    n = sum(len(args.providers) * len(DIRECT_PROMPTS if m == "direct"
                                      else CODEGEN_PROMPTS) for m in args.modes)
    kosten = sum(len(args.providers) * 3 * KOSTEN[m] for m in args.modes)
    print(f"{n} Laeufe ueber {len(args.modes)} Modus/Modi, "
          f"geschaetzt ${kosten:.2f}\n")
    if args.estimate_only:
        return

    ergebnisse = run_all_composite(args.providers, args.seed, args.modes,
                                   attempts=args.attempts, rep=args.rep,
                                   max_tokens=args.max_tokens)

    print("\n" + "=" * 66)
    print("ZUSAMMENFASSUNG")
    ok = [r for r in ergebnisse if r["status"] == "ok"]
    print(f"  {len(ok)}/{len(ergebnisse)} verwertbar, "
          f"${sum(r['cost_usd'] for r in ergebnisse):.2f}")
    for m in args.modes:
        teil = [r for r in ergebnisse if r["mode"] == m]
        if not teil:
            continue
        mittel = sum(r["accuracy"] or 0.0 for r in teil) / len(teil)
        # Wie oft wurden die Laender tatsaechlich vereinheitlicht?
        sauber = sum(1 for r in teil if (r.get("n_country_codes") or 99) <= 12)
        print(f"  {m:9} Ø {mittel:.3f}   Laender vereinheitlicht: "
              f"{sauber}/{len(teil)}")


if __name__ == "__main__":
    main()
