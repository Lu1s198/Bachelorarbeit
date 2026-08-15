"""Entfernt unbrauchbare Ergebnis-Datensaetze eines Seeds.

Notwendig, weil jeder Lauf eine eigene Datei mit Zeitstempel schreibt: Ein
Neustart ueberschreibt einen gescheiterten Lauf nicht, sondern legt eine zweite
Datei daneben. Beide werden anschliessend geladen, und die gescheiterten ziehen
jeden Mittelwert nach unten.

Anzeigen (loescht nichts):
    python scripts/clean_runs.py --seed 2
    python scripts/clean_runs.py --seed 2 --all

Tatsaechlich loeschen:
    python scripts/clean_runs.py --seed 2 --apply
"""

import argparse
import json
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "src"))

from config import settings  # noqa: E402

# Fehlertexte, die kein inhaltliches Scheitern des Modells sind, sondern einen
# Zugangs- oder Abrechnungsfehler. Solche Laeufe duerfen nicht als Ergebnis
# 0 in die Auswertung eingehen -- sie haben nie stattgefunden.
INFRASTRUKTUR = ("credit balance", "authentication_error", "invalid_api_key",
                 "permission_error", "insufficient_quota", "billing")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--providers", nargs="+", default=None,
                        help="Default: alle")
    parser.add_argument("--all", action="store_true",
                        help="alle Laeufe des Seeds entfernen, nicht nur die "
                             "an der Infrastruktur gescheiterten (Baseline bleibt)")
    parser.add_argument("--apply", action="store_true",
                        help="tatsaechlich loeschen; ohne dieses Flag nur anzeigen")
    args = parser.parse_args()

    wurzel = settings.results_dir / str(args.seed)
    if not wurzel.is_dir():
        print(f"{wurzel} existiert nicht.")
        return

    treffer = []
    for p in sorted(wurzel.glob("*/*.json")):
        if p.name == "baseline.json":
            continue                      # regelbasiert, nie betroffen
        text = p.read_text(encoding="utf-8")
        d = json.loads(text)
        if args.providers and d.get("provider") not in args.providers:
            continue
        grund = None
        if args.all:
            grund = "alle"
        elif any(m in text for m in INFRASTRUKTUR):
            grund = "Infrastruktur"
        if grund:
            treffer.append((p, d, grund))

    if not treffer:
        print("Nichts zu entfernen.")
        return

    from collections import Counter
    c = Counter(d.get("provider") for _, d, _ in treffer)
    print(f"{len(treffer)} Datensaetze betroffen: {dict(c)}")
    for p, d, _ in treffer[:5]:
        print(f"   {p.parent.name}/{p.name[:60]}")
    if len(treffer) > 5:
        print(f"   ... und {len(treffer) - 5} weitere")

    if not args.apply:
        print("\nNur Anzeige. Mit --apply tatsaechlich loeschen.")
        return

    for p, d, _ in treffer:
        p.unlink()
        # Der zugehoerige Arbeitsordner (script.py, output.parquet) traegt den
        # Dateinamen ohne Zeitstempel; er wird mitentfernt, damit keine
        # verwaisten Ausgaben zurueckbleiben.
        lauf = (f"{d.get('provider')}_{d.get('prompt_id')}_{d.get('task_id')}"
                f"_r{d.get('repetition')}")
        ordner = p.parent / lauf
        if ordner.is_dir():
            for f in ordner.iterdir():
                f.unlink()
            ordner.rmdir()
    print(f"\n{len(treffer)} Datensaetze entfernt.")


if __name__ == "__main__":
    main()
