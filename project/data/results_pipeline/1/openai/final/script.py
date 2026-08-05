import os
import numpy as np
import pandas as pd

customers_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/dedup_hard/output.parquet"
products_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/products/output.parquet"
orders_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/orders/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/final/output.parquet"

customers = pd.read_parquet(customers_path)
products = pd.read_parquet(products_path)
orders = pd.read_parquet(orders_path)

for frame, column in (
    (customers, "customer_id"),
    (products, "product_id"),
    (orders, "customer_id"),
    (orders, "product_id"),
):
    frame[column] = frame[column].astype("string").str.strip()

customers = customers[["customer_id", "country"]].copy()
customers = customers.rename(columns={"country": "country_code"})

products = products[["product_id", "category"]].copy()

merged = orders.merge(
    customers,
    on="customer_id",
    how="inner",
    validate="many_to_one",
)

merged = merged.merge(
    products,
    on="product_id",
    how="inner",
    validate="many_to_one",
)

merged["quantity"] = pd.to_numeric(merged["quantity"], errors="coerce")
merged["unit_price_eur"] = pd.to_numeric(merged["unit_price_eur"], errors="coerce")
merged["total_revenue_eur"] = merged["quantity"] * merged["unit_price_eur"]

grouped = (
    merged.groupby(["country_code", "category"], dropna=False, as_index=False)
    .agg(
        total_revenue_eur=("total_revenue_eur", "sum"),
        order_count=("customer_id", "size"),
    )
    .sort_values("total_revenue_eur", ascending=False, kind="stable")
    .reset_index(drop=True)
)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
grouped.to_parquet(output_path, index=False)