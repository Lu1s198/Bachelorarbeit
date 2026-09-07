"""Validiert den erzeugten Datensatz gegen die Anforderungen aus Kapitel 5.

Geprüft werden vier Dinge:

1. Die saubere Referenz ist strikt schemakonform. Jede Zeile wird gegen die
   Pydantic-Modelle aus ``dataset.schemas`` validiert.
2. Die eingebauten Qualitätsprobleme liegen tatsächlich vor. Für jede der neun
   Aufgaben wird geprüft, dass der Mangel, an dem sie ansetzt, im Rohdatensatz
   vorhanden ist.
3. Für jede Aufgabe existiert eine nicht leere Soll-Lösung.
4. Die Generierung ist reproduzierbar. Der Datensatz wird zweimal erzeugt und
   bytegenau verglichen.

Aufruf:
    uv run python scripts/validate_dataset.py --seed 2

Der Rückgabewert ist 0, wenn alle Prüfungen bestehen, sonst 1.
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from dataset.generator import generate_full_dataset  # noqa: E402
from dataset.schemas import (  # noqa: E402
    CANONICAL_COUNTRIES,
    CleanCustomer,
    CleanProduct,
)

TASKS = [
    "cleaning_easy_missing_and_whitespace",
    "cleaning_medium_date_formats",
    "cleaning_hard_semantic_unification",
    "dedup_easy_exact_duplicates",
    "dedup_medium_key_duplicates",
    "dedup_hard_fuzzy_duplicates",
    "transform_easy_type_conversion",
    "transform_medium_derived_columns",
    "transform_hard_join_and_aggregate",
]

fehler: list[str] = []


def pruefe(bedingung: bool, text: str) -> None:
    print(f'  {"ok  " if bedingung else "FEHL"}  {text}')
    if not bedingung:
        fehler.append(text)


def _formate(werte: pd.Series, muster: dict[str, str]) -> set[str]:
    gefunden = set()
    for v in werte.dropna().astype(str):
        for name, regex in muster.items():
            if re.fullmatch(regex, v.strip()):
                gefunden.add(name)
    return gefunden


def main(seed: int) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        eins, zwei = Path(tmp) / "a", Path(tmp) / "b"
        pfade = generate_full_dataset(seed=seed, synthetic_dir=eins, ground_truth_dir=eins)
        generate_full_dataset(seed=seed, synthetic_dir=zwei, ground_truth_dir=zwei)
        a_dir, b_dir = eins / str(seed), zwei / str(seed)

        kunden_roh = pd.read_csv(pfade["customers_raw"], dtype=str, keep_default_na=False, na_values=[""])
        produkte_roh = pd.read_csv(pfade["products_raw"], dtype=str, keep_default_na=False, na_values=[""])
        bestellungen = pd.read_csv(pfade["orders_raw"])
        gt_dir = REPO / "data" / "ground_truth" / str(seed)
        kunden_rein = pd.read_csv(gt_dir / "customers_clean.csv")
        produkte_rein = pd.read_csv(gt_dir / "products_clean.csv")

        print(f"\n1. Schemakonformität der sauberen Referenz (Startwert {seed})")
        for name, df, modell in [("customers_clean", kunden_rein, CleanCustomer),
                                 ("products_clean", produkte_rein, CleanProduct)]:
            verstoesse = []
            for i, zeile in enumerate(df.to_dict(orient="records")):
                try:
                    modell.model_validate(zeile)
                except Exception as exc:  # pydantic.ValidationError
                    verstoesse.append(f"Zeile {i}: {exc}")
            pruefe(not verstoesse, f"{name}: {len(df)} Zeilen, {len(verstoesse)} Schemaverstöße")

        print("\n2. Eingebaute Qualitätsprobleme je Aufgabe")
        namen = kunden_roh["full_name"].dropna().astype(str)
        pruefe((namen != namen.str.strip()).any(), "cleaning_easy: Randleerzeichen in full_name")
        pruefe(kunden_roh["country"].isna().any(), "cleaning_easy: fehlende Werte in country")

        datumsformate = _formate(kunden_roh["registered_at"], {
            "ISO": r"\d{4}-\d{2}-\d{2}",
            "deutsch": r"\d{2}\.\d{2}\.\d{4}",
            "US": r"\d{2}/\d{2}/\d{4}",
            "lang": r"[A-Za-z]+ \d{1,2},? \d{4}",
        })
        pruefe(len(datumsformate) >= 2, f"cleaning_medium: {len(datumsformate)} Datumsformate {sorted(datumsformate)}")

        kanonisch = set(CANONICAL_COUNTRIES)
        varianten = {v for v in kunden_roh["country"].dropna().astype(str) if v not in kanonisch}
        pruefe(len(varianten) > 0, f"cleaning_hard: {len(varianten)} nicht-kanonische Länderangaben")

        pruefe(kunden_roh.duplicated(keep=False).any(), "dedup_easy: vollständig identische Zeilen")
        pruefe(kunden_roh["customer_id"].duplicated().any(), "dedup_medium: mehrfache customer_id")
        pruefe(len(kunden_roh) > len(kunden_rein), "dedup_hard: zusätzliche Datensätze gegenüber der Referenz")

        preisformate = _formate(produkte_roh["price_eur"], {
            "punkt": r"\d+\.\d{2}", "komma": r"\d+,\d{2}",
            "waehrung": r".*[€$].*", "text": r".*[A-Za-z].*",
        })
        boolformate = set(produkte_roh["in_stock"].dropna().astype(str).str.lower().unique())
        pruefe(len(preisformate) >= 2 or len(boolformate) > 2,
               f"transform_easy: {len(preisformate)} Preisformate, {len(boolformate)} Wahrheitswert-Schreibweisen")
        pruefe("total_eur" not in bestellungen.columns,
               "transform_medium: total_eur fehlt in den Rohdaten und ist damit abzuleiten")
        offen = set(bestellungen["product_id"]) - set(produkte_rein["product_id"])
        pruefe(not offen, "transform_hard: alle Produktschlüssel der Bestellungen auflösbar")

        print("\n3. Soll-Lösung je Aufgabe (abgelegte Referenz)")
        gt = REPO / "data" / "ground_truth" / str(seed)
        for t in TASKS:
            datei = gt / f"{t}.parquet"
            vorhanden = datei.exists() and len(pd.read_parquet(datei)) > 0
            pruefe(vorhanden, f"{t}: Soll-Lösung vorhanden und nicht leer")
        for name in ("customers_clean.csv", "products_clean.csv"):
            abgelegt = gt / name
            pruefe(abgelegt.exists() and abgelegt.read_bytes() == (a_dir / name).read_bytes(),
                   f"{name}: abgelegte Referenz stimmt mit der neu erzeugten überein")

        print("\n4. Reproduzierbarkeit der Generierung")
        gleich = True
        dateien = sorted(x.name for x in a_dir.iterdir() if x.is_file())
        pruefe(len(dateien) >= 5, f"{len(dateien)} erzeugte Dateien je Lauf")
        for datei in dateien:
            if (a_dir / datei).read_bytes() != (b_dir / datei).read_bytes():
                gleich = False
                print(f"        Abweichung in {datei}")
        pruefe(gleich, "zwei Läufe mit identischem Startwert liefern bytegleiche Dateien")

    print()
    if fehler:
        print(f"FEHLGESCHLAGEN: {len(fehler)} Prüfung(en)")
        return 1
    print("Alle Prüfungen bestanden.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=2)
    raise SystemExit(main(parser.parse_args().seed))
