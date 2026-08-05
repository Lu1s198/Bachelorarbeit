import os
import pandas as pd
import numpy as np

customers_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/dedup_hard/output.parquet"
products_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/products/output.parquet"
orders_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/orders/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/final/output.parquet"

customers = pd.read_parquet(customers_path)
products = pd.read_parquet(products_path)
orders = pd.read_parquet(orders_path)

def normalize_key(series):
    return series.astype("string").str.strip()

customers = customers.copy()
products = products.copy()
orders = orders.copy()

customers["customer_id"] = normalize_key(customers["customer_id"])
products["product_id"] = normalize_key(products["product_id"])
orders["customer_id"] = normalize_key(orders["customer_id"])
orders["product_id"] = normalize_key(orders["product_id"])

customers["country_code"] = customers["country"].astype("string").str.strip().str.upper()
products["category"] = products["category"].astype("string").str.strip()

customers = customers.loc[
    customers["customer_id"].notna()
    & customers["customer_id"].ne("")
    & customers["country_code"].notna()
    & customers["country_code"].str.fullmatch(r"[A-Z]{2}", na=False)
].copy()

products = products.loc[
    products["product_id"].notna()
    & products["product_id"].ne("")
    & products["category"].notna()
    & products["category"].ne("")
].copy()

orders = orders.loc[
    orders["customer_id"].notna()
    & orders["customer_id"].ne("")
    & orders["product_id"].notna()
    & orders["product_id"].ne("")
].copy()

merged = orders.merge(
    customers[["customer_id", "country_code"]],
    on="customer_id",
    how="inner",
)

merged = merged.merge(
    products[["product_id", "category"]],
    on="product_id",
    how="inner",
)

merged["quantity"] = pd.to_numeric(merged["quantity"], errors="coerce")
merged["unit_price_eur"] = pd.to_numeric(merged["unit_price_eur"], errors="coerce")
merged["revenue"] = merged["quantity"] * merged["unit_price_eur"]

result = (
    merged.groupby(["country_code", "category"], as_index=False, dropna=True)
    .agg(
        total_revenue_eur=("revenue", "sum"),
        order_count=("revenue", "size"),
    )
    .sort_values(
        ["total_revenue_eur", "country_code", "category"],
        ascending=[False, True, True],
        kind="mergesort",
    )
    .reset_index(drop=True)
)

result["order_count"] = result["order_count"].astype("int64")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)