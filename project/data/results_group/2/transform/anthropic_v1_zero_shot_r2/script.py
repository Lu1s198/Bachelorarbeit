import pandas as pd
import numpy as np
import re

products_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv"
orders_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/orders_raw.csv"
customers_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_hard/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/transform/anthropic_v1_zero_shot_r2/output.parquet"

products = pd.read_csv(products_path)
orders = pd.read_csv(orders_path)
customers = pd.read_parquet(customers_path)

# Step 1: convert price_eur to float
def parse_price(val):
    if pd.isna(val):
        return np.nan
    s = str(val)
    s = s.replace("€", "").replace("EUR", "").replace("eur", "").strip()
    s = s.replace(" ", "")
    # remove thousand separators, handle decimal comma
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return np.nan

products["price_eur"] = products["price_eur"].apply(parse_price)

def parse_bool(val):
    if pd.isna(val):
        return np.nan
    s = str(val).strip().lower()
    if s in ("ja", "true", "1", "yes", "y"):
        return True
    if s in ("nein", "false", "0", "no", "n"):
        return False
    return np.nan

products["in_stock"] = products["in_stock"].apply(parse_bool)

# Step 2: total_eur, order_year, order_month
orders["total_eur"] = orders["quantity"] * orders["unit_price_eur"]
orders["ordered_at_parsed"] = pd.to_datetime(orders["ordered_at"], errors="coerce")
orders["order_year"] = orders["ordered_at_parsed"].dt.year.astype("Int64")
orders["order_month"] = orders["ordered_at_parsed"].dt.month.astype("Int64")

# Step 3: merge
merged = orders.merge(customers, on="customer_id", how="inner")
merged = merged.merge(products, on="product_id", how="inner")

merged["country_code"] = merged["country"]

valid = merged[
    merged["country_code"].notna() & (merged["country_code"].astype(str).str.strip() != "") &
    merged["category"].notna() & (merged["category"].astype(str).str.strip() != "")
].copy()

valid["revenue"] = valid["quantity"] * valid["unit_price_eur"]

result = (
    valid.groupby(["country_code", "category"], as_index=False)
    .agg(total_revenue_eur=("revenue", "sum"), order_count=("order_id", "count"))
    .sort_values("total_revenue_eur", ascending=False)
    .reset_index(drop=True)
)

result.to_parquet(output_path, index=False)