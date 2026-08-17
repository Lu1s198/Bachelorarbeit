# ETL Task: Transform product, order, and customer data
# Step-by-step breakdown:
# 1. Load all three input files (products CSV, orders CSV, customers Parquet)
#    - Clean price_eur (text -> float) and in_stock (text -> bool) in products
# 2. Compute total_eur in orders, extract order_year and order_month from ordered_at
# 3. Merge customers + products + orders (inner joins), derive country_code,
#    aggregate total_revenue_eur and order_count per (country_code, category),
#    filter invalid country_code/category, sort descending by total_revenue_eur

import pandas as pd
import numpy as np
import re

# -----------------------------
# File paths
# -----------------------------
products_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv"
orders_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/orders_raw.csv"
customers_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_hard/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/transform/anthropic_v3_chain_of_thought_r2/output.parquet"

# -----------------------------
# Load raw data
# -----------------------------
products = pd.read_csv(products_path)
orders = pd.read_csv(orders_path)
customers = pd.read_parquet(customers_path)

# =========================================================
# STEP 1: Clean price_eur -> float, in_stock -> bool
# =========================================================

def parse_price(val):
    # Handle NaN / missing values
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    # Remove currency symbols and text like "EUR", "€"
    s = s.replace("€", "").replace("EUR", "").replace("eur", "")
    s = s.strip()
    # Handle German-style decimal comma vs. dot
    # If both comma and dot exist, assume comma is decimal separator (e.g. "1.234,56")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    # Remove any remaining whitespace
    s = s.replace(" ", "")
    try:
        return float(s)
    except ValueError:
        return np.nan

products["price_eur"] = products["price_eur"].apply(parse_price)

def parse_bool(val):
    # Handle NaN / missing values
    if pd.isna(val):
        return np.nan
    s = str(val).strip().lower()
    true_values = {"ja", "true", "1", "yes", "y", "wahr"}
    false_values = {"nein", "false", "0", "no", "n", "falsch"}
    if s in true_values:
        return True
    elif s in false_values:
        return False
    else:
        return np.nan

products["in_stock"] = products["in_stock"].apply(parse_bool)

# =========================================================
# STEP 2: Compute total_eur, extract order_year/order_month
# =========================================================

orders["total_eur"] = orders["quantity"] * orders["unit_price_eur"]

# Parse ordered_at to datetime (robust to various formats)
orders["ordered_at_parsed"] = pd.to_datetime(orders["ordered_at"], errors="coerce", utc=True)

orders["order_year"] = orders["ordered_at_parsed"].dt.year.astype("Int64")
orders["order_month"] = orders["ordered_at_parsed"].dt.month.astype("Int64")

# Drop helper column (not required in final output, but keep intermediate clean)
orders = orders.drop(columns=["ordered_at_parsed"])

# =========================================================
# STEP 3: Merge customers, products, orders; aggregate
# =========================================================

# Inner join orders with customers on customer_id
merged = orders.merge(customers, on="customer_id", how="inner")

# Inner join result with products on product_id
merged = merged.merge(products, on="product_id", how="inner")

# country already contains ISO code -> rename to country_code
merged["country_code"] = merged["country"]

# Recompute total_eur here for aggregation consistency (quantity * unit_price_eur)
merged["line_revenue"] = merged["quantity"] * merged["unit_price_eur"]

# Filter: keep only rows with valid (non-null, non-empty) country_code and category
merged["country_code"] = merged["country_code"].astype(str).str.strip()
merged["category"] = merged["category"].astype(str).str.strip()

valid_mask = (
    merged["country_code"].notna()
    & (merged["country_code"] != "")
    & (merged["country_code"].str.lower() != "nan")
    & merged["category"].notna()
    & (merged["category"] != "")
    & (merged["category"].str.lower() != "nan")
)

filtered = merged[valid_mask]

# Aggregate: total_revenue_eur and order_count per (country_code, category)
agg = (
    filtered.groupby(["country_code", "category"], as_index=False)
    .agg(
        total_revenue_eur=("line_revenue", "sum"),
        order_count=("order_id", "count"),
    )
)

# Sort descending by total_revenue_eur
result = agg.sort_values("total_revenue_eur", ascending=False).reset_index(drop=True)

# -----------------------------
# Write result to Parquet
# -----------------------------
result.to_parquet(output_path, index=False)