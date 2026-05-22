"""Generate Synthetic Dataset

Clean Data first, then add issues to create a realistic "raw" dataset:

Reproducability: Seeds, same Seed = same Data

Usage:
    from dataset.generator import generate_full_dataset
    generate_full_dataset(seed=42)
"""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pandas as pd
from faker import Faker

from config import settings
from dataset.schemas import CANONICAL_CATEGORIES, CANONICAL_COUNTRIES


# ----- config -----

N_CUSTOMERS_CLEAN = 500                # Correct Customers
N_EXACT_DUPLICATES = 20                 # Exact Dulicates(4%)  
N_FUZZY_DUPLICATES = 20                 # Fuzzy-Duplicates(4%)
N_PRODUCTS = 100                        # Products
N_ORDERS = 2000                         # Orders


# ----- helper functions -----

def _create_dirty_country(clean_code: str, rng: random.Random) -> str:
    """Clean ISO-Code --> Dirty Country Name"""
    mapping = {
        "DE": ["DE", "Deutschland", "Germany", "deutschland", "GER", "Deutshcland"],
        "AT": ["AT", "Österreich", "Austria", "OEsterreich", "AUT"],
        "CH": ["CH", "Schweiz", "Switzerland", "schweiz", "SUI"],
        "FR": ["FR", "Frankreich", "France", "FRA"],
        "IT": ["IT", "Italien", "Italy", "ITA"],
        "ES": ["ES", "Spanien", "Spain", "ESP"],
        "NL": ["NL", "Niederlande", "Netherlands", "Holland"],
        "BE": ["BE", "Belgien", "Belgium"],
        "PL": ["PL", "Polen", "Poland"],
        "GB": ["GB", "Großbritannien", "United Kingdom", "UK", "England"],
    }
    return rng.choice(mapping.get(clean_code, [clean_code]))


def _create_dirty_date(clean_date: date, rng: random.Random) -> str:
    """Clean Date --> Dirty Date Format"""
    fmt = rng.choice(["iso", "de", "us", "unix"])
    if fmt == "iso":
        return clean_date.isoformat()
    if fmt == "de":
        return clean_date.strftime("%d.%m.%Y")
    if fmt == "us":
        return clean_date.strftime("%B %d %Y")
    # unix
    ts = int(datetime.combine(clean_date, datetime.min.time(), tzinfo=timezone.utc).timestamp())
    return str(ts)


def _create_dirty_price(clean_price: Decimal, rng: random.Random) -> str:
    """Clean Price --> Dirty Price Format"""
    fmt = rng.choice(["de_comma", "euro_prefix", "eur_suffix", "plain"])
    if fmt == "de_comma":
        return f"{clean_price}".replace(".", ",")
    if fmt == "euro_prefix":
        return f"€{clean_price}"
    if fmt == "eur_suffix":
        return f"{clean_price} EUR"
    return f"{clean_price}"


def _create_dirty_bool(clean: bool, rng: random.Random) -> str:
    """Clean Boolean --> Dirty Text Representation"""
    if clean:
        return rng.choice(["true", "1", "yes"])
    return rng.choice(["false", "0", "no"])


def _fuzzy_name(clean_name: str, rng: random.Random) -> str:
    """Creates a fuzzy variant of a name"""
    op = rng.choice(["lower", "upper", "swap", "extra_space", "middle_initial"])
    if op == "lower":
        return clean_name.lower()
    if op == "upper":
        return clean_name.upper()
    if op == "swap" and len(clean_name) > 3:
        i = rng.randint(1, len(clean_name) - 2)
        return clean_name[:i] + clean_name[i + 1] + clean_name[i] + clean_name[i + 2:]
    if op == "extra_space":
        return clean_name.replace(" ", "  ")
    if op == "middle_initial":
        parts = clean_name.split(" ", 1)
        return f"{parts[0]} X. {parts[1]}" if len(parts) == 2 else clean_name
    return clean_name


def _fuzzy_email(clean_email: str, rng: random.Random) -> str:
    """Creates a fuzzy variant of an email address."""
    op = rng.choice(["upper", "dots_in_local", "trailing_space"])
    local, domain = clean_email.split("@")
    if op == "upper":
        return f"{local.upper()}@{domain}"
    if op == "dots_in_local" and len(local) > 2:
        i = len(local) // 2
        return f"{local[:i]}.{local[i:]}@{domain}"
    return f" {clean_email} "


# ----- generation -----

def _generate_clean_customers(rng: random.Random, fake: Faker) -> pd.DataFrame:
    rows = []
    for cid in range(1, N_CUSTOMERS_CLEAN + 1):
        rows.append({
            "customer_id": cid,
            "full_name": fake.name(),
            "email": fake.email(),
            "country_code": rng.choice(CANONICAL_COUNTRIES),
            "registered_at": fake.date_between(start_date=date(2020, 1, 1), end_date=date(2025, 12, 31)),
        })
    return pd.DataFrame(rows)


def _make_customers_raw(clean: pd.DataFrame, rng: random.Random) -> pd.DataFrame:
    """Creates a dirty version of the clean customer data and adds duplicates."""
    dirty = clean.copy()

    # rename columns
    dirty = dirty.rename(columns={"country_code": "country"})

    # distort country codes
    dirty["country"] = dirty["country"].apply(lambda c: _create_dirty_country(c, rng))

    # distort dates
    dirty["registered_at"] = dirty["registered_at"].apply(lambda d: _create_dirty_date(d, rng))

    # extra whitespace in names
    mask = [rng.random() < 0.15 for _ in range(len(dirty))]
    dirty.loc[mask, "full_name"] = "  " + dirty.loc[mask, "full_name"] + "  "

    # missing values for country
    mask = [rng.random() < 0.08 for _ in range(len(dirty))]
    dirty.loc[mask, "country"] = None

    # add exact duplicates
    exact_dupes = dirty.sample(n=N_EXACT_DUPLICATES, random_state=rng.randint(0, 10_000)).copy()

    # add fuzzy duplicates
    fuzzy_source = dirty.sample(n=N_FUZZY_DUPLICATES, random_state=rng.randint(0, 10_000)).copy()
    fuzzy_dupes = fuzzy_source.copy()
    fuzzy_dupes["customer_id"] = range(
        dirty["customer_id"].max() + 1,
        dirty["customer_id"].max() + 1 + len(fuzzy_dupes),
    )
    fuzzy_dupes["full_name"] = fuzzy_dupes["full_name"].apply(lambda n: _fuzzy_name(n.strip(), rng))
    fuzzy_dupes["email"] = fuzzy_dupes["email"].apply(lambda e: _fuzzy_email(e, rng))

    combined = pd.concat([dirty, exact_dupes, fuzzy_dupes], ignore_index=True)
    return combined.sample(frac=1.0, random_state=rng.randint(0, 10_000)).reset_index(drop=True)


def _generate_products(rng: random.Random, fake: Faker) -> tuple[pd.DataFrame, pd.DataFrame]:
    clean_rows = []
    for pid in range(1, N_PRODUCTS + 1):
        clean_rows.append({
            "product_id": pid,
            "name": fake.unique.catch_phrase(),
            "category": rng.choice(CANONICAL_CATEGORIES),
            "price_eur": Decimal(f"{rng.uniform(5, 500):.2f}"),
            "in_stock": rng.random() > 0.2,
        })
    clean = pd.DataFrame(clean_rows)

    dirty = clean.copy()
    dirty["price_eur"] = dirty["price_eur"].apply(lambda p: _create_dirty_price(p, rng))
    dirty["in_stock"] = dirty["in_stock"].apply(lambda b: _create_dirty_bool(b, rng))
    return clean, dirty


def _generate_orders(
    clean_customers: pd.DataFrame, clean_products: pd.DataFrame, rng: random.Random
) -> pd.DataFrame:
    rows = []
    customer_ids = clean_customers["customer_id"].tolist()
    for oid in range(1, N_ORDERS + 1):
        pid = rng.randint(1, N_PRODUCTS)
        unit_price = clean_products.loc[clean_products["product_id"] == pid, "price_eur"].iloc[0]
        ordered_at = date(2024, 1, 1) + timedelta(days=rng.randint(0, 365))
        rows.append({
            "order_id": oid,
            "customer_id": rng.choice(customer_ids),
            "product_id": pid,
            "quantity": rng.randint(1, 5),
            "unit_price_eur": float(unit_price),
            "ordered_at": ordered_at.isoformat(),
        })
    return pd.DataFrame(rows)


# ----- full dataset -----

def generate_full_dataset(
    seed: int | None = None,
    synthetic_dir: Path | None = None,
    ground_truth_dir: Path | None = None,
) -> dict[str, Path]:
    """Generates dataset and saves as CSV under data/<...>/<seed>/.

    Returns: mapping of table names to file paths.
    """
    seed = seed if seed is not None else settings.random_seed

    synthetic_dir    = (synthetic_dir    or settings.synthetic_dir)    / str(seed)
    ground_truth_dir = (ground_truth_dir or settings.ground_truth_dir) / str(seed)
    synthetic_dir.mkdir(parents=True, exist_ok=True)
    ground_truth_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(seed)
    fake = Faker("de_DE")
    Faker.seed(seed)

    clean_customers = _generate_clean_customers(rng, fake)
    raw_customers   = _make_customers_raw(clean_customers, rng)
    clean_products, raw_products = _generate_products(rng, fake)
    raw_orders      = _generate_orders(clean_customers, clean_products, rng)

    paths = {
        "customers_raw":   synthetic_dir    / "customers_raw.csv",
        "products_raw":    synthetic_dir    / "products_raw.csv",
        "orders_raw":      synthetic_dir    / "orders_raw.csv",
        "customers_clean": ground_truth_dir / "customers_clean.csv",
        "products_clean":  ground_truth_dir / "products_clean.csv",
    }
    raw_customers.to_csv(paths["customers_raw"], index=False)
    raw_products.to_csv(paths["products_raw"], index=False)
    raw_orders.to_csv(paths["orders_raw"], index=False)
    clean_customers.to_csv(paths["customers_clean"], index=False)
    clean_products.to_csv(paths["products_clean"], index=False)

    return paths
