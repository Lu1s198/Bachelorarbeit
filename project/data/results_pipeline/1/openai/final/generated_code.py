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

customers["customer_id"] = customers["customer_id"].astype("string")
orders["customer_id"] = orders["customer_id"].astype("string")
products["product_id"] = products["product_id"].astype("string")
orders["product_id"] = orders["product_id"].astype("string")

customers = customers[["customer_id", "country"]].copy()
customers = customers.rename(columns={"country": "country_code"})
products = products[["product_id", "category"]].copy()

merged = orders.merge(customers, on="customer_id", how="inner")
merged = merged.merge(products, on="product_id", how="inner")

merged["quantity"] = pd.to_numeric(merged["quantity"], errors="coerce").fillna(0)
merged["unit_price_eur"] = pd.to_numeric(merged["unit_price_eur"], errors="coerce").fillna(0)
merged["revenue"] = merged["quantity"] * merged["unit_price_eur"]

result = (
    merged.groupby(["country_code", "category"], dropna=False, as_index=False)
    .agg(
        total_revenue_eur=("revenue", "sum"),
        order_count=("revenue", "size")
    )
    .sort_values("total_revenue_eur", ascending=False, kind="stable")
    .reset_index(drop=True)
)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)