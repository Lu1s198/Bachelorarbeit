# ============================================================
# ETL Task: Transform products, orders, customers -> revenue aggregation
# ============================================================

import pandas as pd
import numpy as np
import re

# ------------------------------------------------------------
# Sub-steps overview:
# 1. Load all three input files (products, orders, customers)
# 2. Step 1: Clean products.price_eur -> float, products.in_stock -> bool
# 3. Step 2: Compute orders.total_eur, extract order_year, order_month from ordered_at
# 4. Step 3: Merge customers + products + orders on IDs, derive country_code,
#            aggregate by country_code & category -> total_revenue_eur, order_count
#            Sort descending by total_revenue_eur
# 5. Write result to parquet
# ------------------------------------------------------------

# --- Load data ---
products_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv"
orders_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/orders_raw.csv"
customers_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_hard/output.parquet"

products = pd.read_csv(products_path)
orders = pd.read_csv(orders_path)
customers = pd.read_parquet(customers_path)

# ============================================================
# STEP 1: Clean price_eur -> float, in_stock -> bool
# ============================================================

def parse_price(val):
    # Handles formats like '19,99', '€19.99', '19.99 EUR'
    if pd.isna(val):
        return np.nan
    s = str(val)
    # Remove currency symbols and text (EUR, €, whitespace)
    s = s.replace("€", "").replace("EUR", "").strip()
    # If comma is used as decimal separator (no dot present), replace comma with dot
    if "," in s and "." not in s:
        s = s.replace(",", ".")
    else:
        # Remove thousand separators (commas) if dot already present as decimal
        s = s.replace(",", "")
    # Extract numeric part just in case of stray characters
    match = re.search(r"[-+]?\d*\.?\d+", s)
    if match:
        return float(match.group())
    return np.nan

def parse_bool(val):
    # Handles 'ja'/'nein', 'true'/'false', '1'/'0'
    if pd.isna(val):
        return np.nan
    s = str(val).strip().lower()
    true_vals = {"ja", "true", "1", "yes", "y"}
    false_vals = {"nein", "false", "0", "no", "n"}
    if s in true_vals:
        return True
    elif s in false_vals:
        return False
    else:
        return np.nan

products["price_eur"] = products["price_eur"].apply(parse_price)
products["in_stock"] = products["in_stock"].apply(parse_bool)

# ============================================================
# STEP 2: Compute total_eur, order_year, order_month
# ============================================================

orders["total_eur"] = orders["quantity"] * orders["unit_price_eur"]

# Parse ordered_at as datetime, extract year and month as integers
orders["ordered_at_parsed"] = pd.to_datetime(orders["ordered_at"], errors="coerce")
orders["order_year"] = orders["ordered_at_parsed"].dt.year
orders["order_month"] = orders["ordered_at_parsed"].dt.month

# Convert to nullable integer type (Int64) to keep them as integers
orders["order_year"] = orders["order_year"].astype("Int64")
orders["order_month"] = orders["order_month"].astype("Int64")

orders = orders.drop(columns=["ordered_at_parsed"])

# ============================================================
# STEP 3: Merge tables, derive country_code, aggregate
# ============================================================

# customers.country already contains ISO country code -> rename to country_code
customers = customers.rename(columns={"country": "country_code"})

# Merge orders with customers (inner join: unmatched customers dropped)
merged = orders.merge(customers[["customer_id", "country_code"]], on="customer_id", how="inner")

# Merge with products (inner join: unmatched products dropped)
merged = merged.merge(products[["product_id", "category"]], on="product_id", how="inner")

# Filter: keep only rows with valid (non-null, non-empty) country_code and category
merged["country_code"] = merged["country_code"].astype(str).str.strip()
merged["category"] = merged["category"].astype(str).str.strip()

valid_mask = (
    merged["country_code"].notna() &
    (merged["country_code"] != "") &
    (merged["country_code"].str.lower() != "nan") &
    merged["category"].notna() &
    (merged["category"] != "") &
    (merged["category"].str.lower() != "nan")
)
merged = merged[valid_mask]

# Aggregate: total_revenue_eur = sum(quantity * unit_price_eur), order_count = number of orders
agg = merged.groupby(["country_code", "category"], as_index=False).agg(
    total_revenue_eur=("total_eur", "sum"),
    order_count=("order_id", "count")
)

# Sort descending by total_revenue_eur
result = agg.sort_values("total_revenue_eur", ascending=False).reset_index(drop=True)

# ============================================================
# Write result to Parquet
# ============================================================

output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/transform/anthropic_v3_chain_of_thought/output.parquet"
result.to_parquet(output_path, index=False)