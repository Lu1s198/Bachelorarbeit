"""Referenzlösungen = Ground Truth für die neun ETL-Aufgaben.

Da der Datensatz kontrolliert erzeugt wird (Kapitel 5), ist die exakte
Soll-Lösung jeder Aufgabe bekannt: Sie ergibt sich aus der Umkehrung der
gezielt eingebrachten Verfälschung. Für die semantischen bzw. mehrstufigen
Aufgaben (Länder-Vereinheitlichung, Fuzzy-Duplikate, Join+Aggregation) wird
dabei privilegiertes Wissen aus der Generierung genutzt (Inverse der
Varianten-Tabelle, die ID-Grenze der Originaldatensätze, die sauberen
Referenztabellen). Genau dieses Wissen steht der klassischen Pipeline und den
LLMs nicht zur Verfügung -- deshalb taugt die Referenz als Ground Truth.

Aufruf:
    from dataset.reference import build_all_ground_truth
    build_all_ground_truth(seed=1)
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from config import settings
from dataset.generator import N_CUSTOMERS_CLEAN
from dataset.schemas import COUNTRY_VARIANTS

# Inverse der Varianten-Tabelle: normalisierte Schreibweise -> ISO-Code.
_COUNTRY_INVERSE: dict[str, str] = {
    variant.strip().lower(): iso
    for iso, variants in COUNTRY_VARIANTS.items()
    for variant in variants
}


# ----- Hilfs-Parser (Umkehrung der Verfälschung) -----

def parse_date_iso(value: object) -> str:
    """Vereinheitlicht die vier erzeugten Datumsformate auf YYYY-MM-DD."""
    s = str(value).strip()
    if s.isdigit() and len(s) >= 8:  # Unix-Timestamp
        return datetime.fromtimestamp(int(s), tz=timezone.utc).date().isoformat()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%B %d %Y"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return pd.to_datetime(s).date().isoformat()


def country_to_iso(value: object) -> str:
    """Bildet eine (verfälschte) Länderangabe auf den ISO-3166-1-alpha-2-Code ab."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "UNKNOWN"
    return _COUNTRY_INVERSE.get(str(value).strip().lower(), "UNKNOWN")


def parse_price(value: object) -> float:
    """Wandelt uneinheitliche Preis-Schreibweisen in einen Float um."""
    s = str(value).strip().replace("€", "").replace("EUR", "").strip()
    s = s.replace(",", ".")
    return round(float(s), 2)


def parse_bool(value: object) -> bool:
    """Wandelt textuelle Wahrheitswerte in einen Boolean um."""
    return str(value).strip().lower() in ("true", "1", "yes", "ja", "wahr")


# ----- Referenzlösungen je Aufgabe -----

def _strip_customer_text_fields(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    for col in ("full_name", "email", "country"):
        cleaned[col] = cleaned[col].str.strip()
    return cleaned

def _cleaning_easy(raw_customers: pd.DataFrame) -> pd.DataFrame:
    df = _strip_customer_text_fields(raw_customers)
    df["country"] = df["country"].fillna("UNKNOWN")
    return df


def _cleaning_medium(raw_customers: pd.DataFrame) -> pd.DataFrame:
    df = _strip_customer_text_fields(raw_customers)
    df["registered_at"] = df["registered_at"].map(parse_date_iso)
    return df


def _cleaning_hard(raw_customers: pd.DataFrame) -> pd.DataFrame:
    df = _strip_customer_text_fields(raw_customers)
    df["country"] = df["country"].map(country_to_iso)
    return df


def _dedup_easy(raw_customers: pd.DataFrame) -> pd.DataFrame:
    return raw_customers.drop_duplicates(keep="first").reset_index(drop=True)


def _dedup_medium(raw_customers: pd.DataFrame) -> pd.DataFrame:
    df = raw_customers.copy()
    df["_parsed"] = df["registered_at"].map(parse_date_iso)
    df = df.sort_values("_parsed", ascending=False, kind="stable")
    df = df.drop_duplicates(subset="email", keep="first")
    return df.drop(columns="_parsed").reset_index(drop=True)


def _dedup_hard(raw_customers: pd.DataFrame) -> pd.DataFrame:
    # Die realen Personen sind exakt die ursprünglichen 500 Datensätze
    # (Fuzzy-Duplikate tragen eine höhere customer_id).
    df = raw_customers[raw_customers["customer_id"] <= N_CUSTOMERS_CLEAN]
    return df.drop_duplicates(keep="first").reset_index(drop=True)


def _transform_easy(raw_products: pd.DataFrame) -> pd.DataFrame:
    df = raw_products.copy()
    df["price_eur"] = df["price_eur"].map(parse_price)
    df["in_stock"] = df["in_stock"].map(parse_bool)
    return df


def _transform_medium(raw_orders: pd.DataFrame) -> pd.DataFrame:
    df = raw_orders.copy()
    df["total_eur"] = df["quantity"] * df["unit_price_eur"]
    dt = pd.to_datetime(df["ordered_at"])
    df["order_year"] = dt.dt.year
    df["order_month"] = dt.dt.month
    return df


def _transform_hard(
    raw_orders: pd.DataFrame,
    clean_customers: pd.DataFrame,
    clean_products: pd.DataFrame,
) -> pd.DataFrame:
    merged = (
        raw_orders.merge(
            clean_customers[["customer_id", "country_code"]], on="customer_id", how="left"
        )
        .merge(clean_products[["product_id", "category"]], on="product_id", how="left")
    )
    merged["_revenue"] = merged["quantity"] * merged["unit_price_eur"]
    grouped = merged.groupby(["country_code", "category"], as_index=False).agg(
        total_revenue_eur=("_revenue", "sum"),
        order_count=("order_id", "count"),
    )
    grouped["total_revenue_eur"] = grouped["total_revenue_eur"].round(2)
    return grouped.sort_values("total_revenue_eur", ascending=False).reset_index(drop=True)


# ----- Orchestrierung -----

def build_all_ground_truth(
    seed: int | None = None,
    synthetic_dir: Path | None = None,
    ground_truth_dir: Path | None = None,
) -> dict[str, Path]:
    """Erzeugt für jede Aufgabe die Soll-Lösung und legt sie als Parquet ab.

    Voraussetzung: der Rohdatensatz (`generate_full_dataset`) wurde zuvor
    unter demselben Seed erzeugt. Rückgabe: task_id -> Pfad der Parquet-Datei.
    """
    from dataset.scenarios import ALL_TASKS  # lazy, um Zyklen zu vermeiden

    seed = seed if seed is not None else settings.random_seed
    synthetic_dir = (synthetic_dir or settings.synthetic_dir) / str(seed)
    ground_truth_dir = (ground_truth_dir or settings.ground_truth_dir) / str(seed)
    ground_truth_dir.mkdir(parents=True, exist_ok=True)

    raw_customers = pd.read_csv(synthetic_dir / "customers_raw.csv")
    raw_products = pd.read_csv(synthetic_dir / "products_raw.csv")
    raw_orders = pd.read_csv(synthetic_dir / "orders_raw.csv")
    clean_customers = pd.read_csv(ground_truth_dir / "customers_clean.csv")
    clean_products = pd.read_csv(ground_truth_dir / "products_clean.csv")

    builders = {
        "cleaning_easy_missing_and_whitespace": lambda: _cleaning_easy(raw_customers),
        "cleaning_medium_date_formats": lambda: _cleaning_medium(raw_customers),
        "cleaning_hard_semantic_unification": lambda: _cleaning_hard(raw_customers),
        "dedup_easy_exact_duplicates": lambda: _dedup_easy(raw_customers),
        "dedup_medium_key_duplicates": lambda: _dedup_medium(raw_customers),
        "dedup_hard_fuzzy_duplicates": lambda: _dedup_hard(raw_customers),
        "transform_easy_type_conversion": lambda: _transform_easy(raw_products),
        "transform_medium_derived_columns": lambda: _transform_medium(raw_orders),
        "transform_hard_join_and_aggregate": lambda: _transform_hard(
            raw_orders, clean_customers, clean_products
        ),
    }

    paths: dict[str, Path] = {}
    for task in ALL_TASKS:
        if task.id not in builders:
            raise KeyError(f"Keine Referenzlösung für Task '{task.id}' hinterlegt")
        df = builders[task.id]()
        out = ground_truth_dir / task.expected_output
        df.to_parquet(out, index=False)
        paths[task.id] = out
    return paths
