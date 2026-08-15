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

customers["customer_id"] = pd.to_numeric(customers["customer_id"], errors="coerce").astype("Int64")
orders["customer_id"] = pd.to_numeric(orders["customer_id"], errors="coerce").astype("Int64")

products["product_id"] = pd.to_numeric(products["product_id"], errors="coerce").astype("Int64")
orders["product_id"] = pd.to_numeric(orders["product_id"], errors="coerce").astype("Int64")

customers = customers.loc[
    customers["customer_id"].notna(),
    ["customer_id", "country"]
].copy()
customers["country_code"] = customers["country"].astype("string").str.strip().str.upper()
customers = customers.loc[
    customers["country_code"].notna() & customers["country_code"].ne(""),
    ["customer_id", "country_code"]
].copy()

products = products.loc[
    products["product_id"].notna(),
    ["product_id", "category"]
].copy()
products["category"] = products["category"].astype("string").str.strip()
products = products.loc[
    products["category"].notna() & products["category"].ne(""),
    ["product_id", "category"]
].copy()

orders = orders.loc[
    orders["customer_id"].notna() & orders["product_id"].notna()
].copy()

merged = orders.merge(
    customers,
    on="customer_id",
    how="inner"
).merge(
    products,
    on="product_id",
    how="inner"
)

merged["quantity"] = pd.to_numeric(merged["quantity"], errors="coerce")
merged["unit_price_eur"] = pd.to_numeric(merged["unit_price_eur"], errors="coerce")
merged["revenue"] = merged["quantity"] * merged["unit_price_eur"]

result = (
    merged.groupby(["country_code", "category"], as_index=False, dropna=False)
    .agg(
        total_revenue_eur=("revenue", "sum"),
        order_count=("order_id", "count")
    )
    .sort_values("total_revenue_eur", ascending=False, kind="stable")
    .reset_index(drop=True)
)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)