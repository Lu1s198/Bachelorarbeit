"""Klassische, regelbasierte ETL-Pipeline (Vergleichsbasis, Kapitel 4.6).

Diese Pipeline löst dieselben neun Aufgaben ausschließlich mit fest
vorgegebenen Regeln und ohne Zugriff auf das privilegierte Wissen der
Generierung. Für die klar formalisierbaren Aufgaben nutzt sie dieselben
deterministischen Routinen wie die Referenz (dort *ist* die Regel die korrekte
Lösung). Für die beiden semantisch geprägten Aufgaben -- Länder-Vereinheitlichung
und Fuzzy-Duplikate -- sowie den mehrstufigen Join arbeitet sie mit realistischen
Heuristiken, die an ihre Grenzen stoßen. Genau dort wird der Unterschied zu den
LLM-gestützten Verfahren messbar (Hypothese H1).
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from config import settings
from dataset import reference as ref

# Bewusst begrenzte Länder-Tabelle: nur volle Namen und ISO-Codes,
# KEINE Tippfehler/Abkürzungen (z.B. 'GER', 'Deutshcland', 'Holland', 'UK').
_LIMITED_COUNTRY_MAP = {
    "de": "DE", "deutschland": "DE", "germany": "DE",
    "at": "AT", "österreich": "AT", "austria": "AT",
    "ch": "CH", "schweiz": "CH", "switzerland": "CH",
    "fr": "FR", "frankreich": "FR", "france": "FR",
    "it": "IT", "italien": "IT", "italy": "IT",
    "es": "ES", "spanien": "ES", "spain": "ES",
    "nl": "NL", "niederlande": "NL", "netherlands": "NL",
    "be": "BE", "belgien": "BE", "belgium": "BE",
    "pl": "PL", "polen": "PL", "poland": "PL",
    "gb": "GB", "großbritannien": "GB", "united kingdom": "GB",
}


def _country_baseline(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "UNKNOWN"
    return _LIMITED_COUNTRY_MAP.get(str(value).strip().lower(), "UNKNOWN")


def _fuzzy_key(name: object, email: object) -> str:
    """Normalisierter Schlüssel für die regelbasierte Fuzzy-Erkennung."""
    n = re.sub(r"\s+", "", str(name)).lower()
    local = str(email).split("@")[0].replace(".", "").lower()
    return f"{n}|{local}"


def _cleaning_hard(raw_customers: pd.DataFrame) -> pd.DataFrame:
    df = ref._strip_customer_text_fields(raw_customers)
    df["country"] = df["country"].map(_country_baseline)
    return df


def _dedup_hard(raw_customers: pd.DataFrame) -> pd.DataFrame:
    df = raw_customers.copy()
    df["_k"] = [_fuzzy_key(n, e) for n, e in zip(df["full_name"], df["email"])]
    df = df.drop_duplicates(subset="_k", keep="first")
    return df.drop(columns="_k").reset_index(drop=True)


def _transform_hard(
    raw_orders: pd.DataFrame,
    raw_customers: pd.DataFrame,
    raw_products: pd.DataFrame,
) -> pd.DataFrame:
    customers = raw_customers.drop_duplicates(subset="customer_id", keep="first").copy()
    customers["country_code"] = customers["country"].map(_country_baseline)
    merged = (
        raw_orders.merge(
            customers[["customer_id", "country_code"]], on="customer_id", how="left"
        )
        .merge(raw_products[["product_id", "category"]], on="product_id", how="left")
    )
    merged["_revenue"] = merged["quantity"] * merged["unit_price_eur"]
    grouped = merged.groupby(["country_code", "category"], as_index=False).agg(
        total_revenue_eur=("_revenue", "sum"),
        order_count=("order_id", "count"),
    )
    grouped["total_revenue_eur"] = grouped["total_revenue_eur"].round(2)
    return grouped.sort_values("total_revenue_eur", ascending=False).reset_index(drop=True)


def run_baseline_task(task_id: str, seed: int | None = None) -> pd.DataFrame:
    """Führt die regelbasierte Lösung einer Aufgabe aus und liefert das Ergebnis."""
    seed = seed if seed is not None else settings.random_seed
    d = settings.synthetic_dir / str(seed)
    raw_customers = pd.read_csv(d / "customers_raw.csv")
    raw_products = pd.read_csv(d / "products_raw.csv")
    raw_orders = pd.read_csv(d / "orders_raw.csv")

    match task_id:
        case "cleaning_easy_missing_and_whitespace":
            return ref._cleaning_easy(raw_customers)
        case "cleaning_medium_date_formats":
            return ref._cleaning_medium(raw_customers)
        case "cleaning_hard_semantic_unification":
            return _cleaning_hard(raw_customers)
        case "dedup_easy_exact_duplicates":
            return ref._dedup_easy(raw_customers)
        case "dedup_medium_key_duplicates":
            return ref._dedup_medium(raw_customers)
        case "dedup_hard_fuzzy_duplicates":
            return _dedup_hard(raw_customers)
        case "transform_easy_type_conversion":
            return ref._transform_easy(raw_products)
        case "transform_medium_derived_columns":
            return ref._transform_medium(raw_orders)
        case "transform_hard_join_and_aggregate":
            return _transform_hard(raw_orders, raw_customers, raw_products)
        case _:
            raise KeyError(f"Unbekannte Task-ID: {task_id}")
