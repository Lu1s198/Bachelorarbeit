"""Schemas of the synthetic dataset.

Simulates small E-Commerce Database with 3 tables:

- 'customers'  - Customer Data (Cleaning, Deduplication)
- 'products'   - Product Catalog (Cleaning, Type Conversion)
- 'orders'     - Orders (Joins, Aggregations)

The schemas are defined as Pydantic models. This allows:
- the target schema for the AI to be machine-readable and documented
- the generation of clean data that strictly adheres to the schema
- a unqiue ground truth for evaluation
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


# ----- Saubere Zielschemata (Ground Truth) -----


class CleanCustomer(BaseModel):
    """Customer Data after ETL-Cleaning"""
    customer_id: int
    full_name: str
    email: str
    country_code: str = Field(min_length=2, max_length=2)
    registered_at: date


class CleanProduct(BaseModel):
    product_id: int
    name: str
    category: str
    price_eur: Decimal = Field(ge=Decimal("0"))
    in_stock: bool


class CleanOrder(BaseModel):
    order_id: int
    customer_id: int
    product_id: int
    quantity: int = Field(ge=1)
    ordered_at: date
    total_eur: Decimal = Field(ge=Decimal("0"))


# ----- Wertelisten für die Generierung -----

CANONICAL_COUNTRIES = ["DE", "AT", "CH", "FR", "IT", "ES", "NL", "BE", "PL", "GB"]
CANONICAL_CATEGORIES = ["Electronics", "Books", "Clothing", "Home", "Sports", "Toys"]

# Varianten je ISO-Code für die kontrollierte Verfälschung der Länderangaben.
# Einzige Quelle der Wahrheit: der Generator streut hieraus, die Referenzlösung
# (dataset/reference.py) invertiert diese Tabelle, um die Soll-Lösung zu bilden.
COUNTRY_VARIANTS: dict[str, list[str]] = {
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
