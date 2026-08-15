"""Erzeugt eine verkleinerte Variante eines bestehenden Datensatzes.

Motivation: Im Direkt-Modus muss das Modell die vollstaendige Ergebnistabelle
zurueckschreiben. Bei 540 Kunden bzw. 2000 Bestellungen stoesst das an das
Ausgabelimit -- mehrere Direkt-Laeufe des Seeds 1 liegen exakt bei 32.000
Completion-Token und sind damit abgeschnitten. Eine halbierte Fassung bleibt
deutlich darunter, enthaelt aber weiterhin jede Problemklasse.

Vorgehen (bewusst kein Neu-Generieren): Aus den Rohdaten wird eine Teilmenge der
*urspruenglichen* Kunden gezogen; deren exakte und unscharfe Duplikate werden
mitgenommen, ebenso alle Bestellungen dieser Kunden. Damit bleiben
- die referenzielle Integritaet (jede Bestellung hat ihren Kunden),
- die Duplikat-Paare vollstaendig (Original + Zwilling),
- die id-Konvention (unscharfe Duplikate tragen ids > N_CUSTOMERS_CLEAN),
sodass die unveraenderte Referenzlogik aus dataset/reference.py weiterhin die
korrekte Soll-Loesung erzeugt. Die Produkttabelle bleibt vollstaendig, sie ist
mit 100 Zeilen ohnehin unkritisch.

Die Auswahl ist **stratifiziert**: Wuerde man die Kunden rein zufaellig ziehen,
verloere man die Duplikat-Paare ueberproportional (ein Paar ueberlebt nur, wenn
sein Original gezogen wurde) und die schluesselbasierte Entdoppelung wuerde
degenerieren. Stattdessen wird je Problemklasse genau der Anteil ``fraction``
ihrer Faelle beibehalten, sodass die Anteile aus Kapitel 5 (je rund vier Prozent
exakte und unscharfe Duplikate) erhalten bleiben.

Aufruf:
    python scripts/make_half_dataset.py                  # Seed 1 -> Seed 101
    python scripts/make_half_dataset.py --fraction 0.5
    python scripts/make_half_dataset.py --source 1 --target 101
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path

import pandas as pd

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "src"))

from config import settings  # noqa: E402
from dataset.generator import N_CUSTOMERS_CLEAN  # noqa: E402
from dataset.reference import build_all_ground_truth  # noqa: E402


# ------------------------------------------------------------------ Paarbildung

def _norm_name(s: object) -> str:
    return " ".join(str(s).split()).lower()


def _norm_local(s: object) -> str:
    return str(s).strip().split("@")[0].replace(".", "").lower()


def _fuzzy_partner(zwilling: pd.Series, originale: pd.DataFrame) -> int | None:
    """Ordnet einem unscharfen Duplikat seinen Ausgangsdatensatz zu.

    Der Generator uebernimmt fuer den Zwilling ``country`` und ``registered_at``
    unveraendert und verfaelscht nur Name und E-Mail. Beide Felder dienen daher
    als harter Filter, innerhalb dessen ueber die Aehnlichkeit von Name und
    E-Mail-Lokalteil eindeutig zugeordnet wird. Eine Zuordnung allein ueber einen
    normalisierten Schluessel wuerde genau die schwierigen Faelle (Tippfehler,
    eingefuegtes Mittelinitial) verfehlen -- also die wertvollsten.
    """
    kandidaten = originale
    for spalte in ("country", "registered_at"):
        gleich = kandidaten[spalte].fillna("__NA__") == (
            zwilling[spalte] if pd.notna(zwilling[spalte]) else "__NA__")
        if gleich.any():
            kandidaten = kandidaten[gleich]
    if kandidaten.empty:
        return None

    n, e = _norm_name(zwilling["full_name"]), _norm_local(zwilling["email"])
    bester, bestwert = None, 0.0
    for r in kandidaten.itertuples():
        wert = (difflib.SequenceMatcher(None, n, _norm_name(r.full_name)).ratio()
                + difflib.SequenceMatcher(None, e, _norm_local(r.email)).ratio())
        if wert > bestwert:
            bester, bestwert = int(r.customer_id), wert
    return bester if bestwert >= 1.2 else None


# ------------------------------------------------------------------ Auswahl

def _stratifizierte_auswahl(customers: pd.DataFrame, fraction: float,
                            seed: int) -> tuple[set[int], dict]:
    """Waehlt die beizubehaltenden Original-Kunden je Problemklasse anteilig."""
    cid = customers["customer_id"].astype(int)
    originale = customers[cid <= N_CUSTOMERS_CLEAN].copy()
    originale["customer_id"] = originale["customer_id"].astype(int)
    zwillinge = customers[cid > N_CUSTOMERS_CLEAN].copy()

    # Eindeutige Originale (ohne die exakten Duplikat-Zeilen)
    eindeutig = originale.drop_duplicates(subset="customer_id", keep="first")
    alle_ids = sorted(eindeutig["customer_id"])

    mit_exaktem_dupe = sorted(set(
        originale["customer_id"][originale.duplicated(keep=False)]))
    paare = {int(z["customer_id"]): _fuzzy_partner(z, eindeutig)
             for _, z in zwillinge.iterrows()}
    mit_fuzzy_dupe = sorted({p for p in paare.values() if p is not None})

    # Schluessel-Duplikate im Sinne von Schritt 5: Der Schritt entfernt Zeilen mit
    # mehrfacher `email` und wirkt daher nur bei den unscharfen Zwillingen, deren
    # E-Mail-Verfaelschung reines Leerzeichen-Rauschen war -- nach der Bereinigung
    # in Schritt 1 ist ihre Adresse mit der des Originals identisch. Zwillinge mit
    # eingefuegtem Punkt oder veraenderter Gross-/Kleinschreibung zaehlen NICHT
    # dazu, sie werden erst von Schritt 6 erfasst. Diese Klasse ist eine echte
    # Teilmenge von `mit_fuzzy_dupe`.
    mail_roh = customers["email"].astype(str).str.strip()
    mit_key_dupe = sorted({
        partner for z_id, partner in paare.items()
        if partner is not None
        and (mail_roh[cid == z_id].iloc[0] == mail_roh[cid == partner].iloc[0])
    })

    def quote(pool: list[int], bereits: set[int]) -> set[int]:
        """Zieht so viele Kunden, dass am Ende genau ``fraction`` der Klasse
        enthalten ist -- bereits ausgewaehlte Mitglieder werden angerechnet.

        Ohne diese Anrechnung wuerden sich ueberlappende Klassen gegenseitig
        aufaddieren und am Ende jede Klasse vollstaendig enthalten sein."""
        ziel_n = round(len(pool) * fraction)
        schon = len(set(pool) & bereits)
        rest = [i for i in pool if i not in bereits]
        n = max(0, min(ziel_n - schon, len(rest)))
        return set(pd.Series(rest).sample(n=n, random_state=seed)) if n else set()

    behalten: set[int] = set()
    # Reihenfolge: engste Klasse zuerst, damit ihre Faelle sicher enthalten sind
    behalten |= quote(mit_key_dupe, behalten)
    behalten |= quote(mit_fuzzy_dupe, behalten)
    behalten |= quote(mit_exaktem_dupe, behalten)

    # Aufgefuellt wird ausschliesslich aus den unauffaelligen Kunden. Wuerde man
    # aus allen ziehen, kaemen zufaellig weitere Duplikat-Originale hinzu und der
    # Duplikatanteil stiege ueber die in Kapitel 5 dokumentierten vier Prozent.
    interessant = set(mit_fuzzy_dupe) | set(mit_exaktem_dupe)
    unauffaellig = [i for i in alle_ids if i not in interessant]
    ziel = round(len(alle_ids) * fraction)
    fehlt = ziel - len(behalten)
    if fehlt > 0:
        behalten |= set(pd.Series(unauffaellig).sample(n=min(fehlt, len(unauffaellig)),
                                                       random_state=seed))

    diagnose = {
        "originale_gesamt": len(alle_ids),
        "mit_exaktem_duplikat": len(mit_exaktem_dupe),
        "mit_unscharfem_duplikat": len(mit_fuzzy_dupe),
        "mit_schluessel_duplikat": len(mit_key_dupe),
        "unscharfe_ohne_zuordnung": sum(1 for p in paare.values() if p is None),
    }
    return behalten, {"paare": paare, "diagnose": diagnose}


# ------------------------------------------------------------------ Hauptlauf

def make_subset(source: int, target: int, fraction: float, seed: int) -> dict:
    src = settings.synthetic_dir / str(source)
    dst = settings.synthetic_dir / str(target)
    dst.mkdir(parents=True, exist_ok=True)

    customers = pd.read_csv(src / "customers_raw.csv", dtype=str)
    products = pd.read_csv(src / "products_raw.csv", dtype=str)
    orders = pd.read_csv(src / "orders_raw.csv", dtype=str)

    behalten, info = _stratifizierte_auswahl(customers, fraction, seed)
    paare = info["paare"]

    cid = customers["customer_id"].astype(int)
    ist_original = cid <= N_CUSTOMERS_CLEAN
    zwilling_behalten = cid.map(lambda i: paare.get(int(i)) in behalten
                                if int(i) > N_CUSTOMERS_CLEAN else False)
    maske = (ist_original & cid.isin(behalten)) | zwilling_behalten

    neue_customers = customers[maske].reset_index(drop=True)
    neue_orders = orders[orders["customer_id"].astype(int).isin(behalten)].reset_index(drop=True)
    neue_orders["order_id"] = range(1, len(neue_orders) + 1)

    neue_customers.to_csv(dst / "customers_raw.csv", index=False)
    products.to_csv(dst / "products_raw.csv", index=False)
    neue_orders.to_csv(dst / "orders_raw.csv", index=False)

    gt_src = settings.ground_truth_dir / str(source)
    gt_dst = settings.ground_truth_dir / str(target)
    gt_dst.mkdir(parents=True, exist_ok=True)
    cc = pd.read_csv(gt_src / "customers_clean.csv", dtype=str)
    cc[cc["customer_id"].astype(int).isin(behalten)].to_csv(
        gt_dst / "customers_clean.csv", index=False)
    pd.read_csv(gt_src / "products_clean.csv", dtype=str).to_csv(
        gt_dst / "products_clean.csv", index=False)

    n_original = int((neue_customers["customer_id"].astype(int) <= N_CUSTOMERS_CLEAN).sum())
    n_zwilling = len(neue_customers) - n_original
    meta = {
        "abgeleitet_von_seed": source,
        "anteil": fraction,
        "auswahl_seed": seed,
        "auswahl": "stratifiziert je Problemklasse",
        "kunden_roh": len(neue_customers),
        "kunden_eindeutig": len(behalten),
        "zeilen_mit_original_id": n_original,
        "unscharfe_duplikate": n_zwilling,
        "produkte": len(products),
        "bestellungen": len(neue_orders),
        "quelle_diagnose": info["diagnose"],
    }
    (dst / "dataset_meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return meta


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=int, default=1, help="Quell-Seed")
    parser.add_argument("--target", type=int, default=101, help="Ziel-Seed")
    parser.add_argument("--fraction", type=float, default=0.5,
                        help="Anteil je Problemklasse (Standard: 0.5)")
    parser.add_argument("--select-seed", type=int, default=42, dest="select_seed",
                        help="Zufallskern der Auswahl (deterministisch)")
    args = parser.parse_args()

    meta = make_subset(args.source, args.target, args.fraction, args.select_seed)
    print(f"Teilmenge geschrieben (Seed {args.source} -> {args.target}):")
    for k, v in meta.items():
        print(f"  {k}: {v}")

    gt = build_all_ground_truth(seed=args.target)
    print("Ground Truth je Aufgabe:")
    for task_id, p in gt.items():
        print(f"  {task_id}: {p.name}")


if __name__ == "__main__":
    main()
