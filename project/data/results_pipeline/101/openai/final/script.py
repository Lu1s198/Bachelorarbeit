import os
import pandas as pd
import numpy as np

customers_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/openai/dedup_hard/output.parquet"
products_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/openai/products/output.parquet"
orders_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/openai/orders/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/openai/final/output.parquet"

customers = pd.read_parquet(customers_path)
products = pd.read_parquet(products_path)
orders = pd.read_parquet(orders_path)

customers["customer_id"] = pd.to_numeric(customers["customer_id"], errors="coerce").astype("Int64")
products["product_id"] = pd.to_numeric(products["product_id"], errors="coerce").astype("Int64")
orders["customer_id"] = pd.to_numeric(orders["customer_id"], errors="coerce").astype("Int64")
orders["product_id"] = pd.to_numeric(orders["product_id"], errors="coerce").astype("Int64")

customers = customers[["customer_id", "country"]].copy()
products = products[["product_id", "category"]].copy()

customers["country_code"] = customers["country"].astype("string").str.strip().str.upper()
products["category"] = products["category"].astype("string").str.strip()

merged = orders.merge(
    customers[["customer_id", "country_code"]],
    on="customer_id",
    how="inner"
).merge(
    products[["product_id", "category"]],
    on="product_id",
    how="inner"
)

merged = merged[
    merged["country_code"].notna()
    & merged["category"].notna()
    & merged["country_code"].ne("")
    & merged["category"].ne("")
].copy()

merged["quantity"] = pd.to_numeric(merged["quantity"], errors="coerce")
merged["unit_price_eur"] = pd.to_numeric(merged["unit_price_eur"], errors="coerce")
merged["revenue"] = merged["quantity"] * merged["unit_price_eur"]

result = (
    merged.groupby(["country_code", "category"], dropna=False, as_index=False)
    .agg(
        total_revenue_eur=("revenue", "sum"),
        order_count=("order_id", "size")
    )
    .sort_values("total_revenue_eur", ascending=False, kind="stable")
    .reset_index(drop=True)
)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)