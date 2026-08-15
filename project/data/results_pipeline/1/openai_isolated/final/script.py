import os
from pathlib import Path
import pandas as pd
import numpy as np

customers_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/_reference/dedup_hard/output.parquet"
products_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/_reference/products/output.parquet"
orders_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/_reference/orders/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai_isolated/final/output.parquet"

customers = pd.read_parquet(customers_path)
products = pd.read_parquet(products_path)
orders = pd.read_parquet(orders_path)

customers["customer_id"] = customers["customer_id"].astype("int64")
products["product_id"] = products["product_id"].astype("int64")
orders["customer_id"] = orders["customer_id"].astype("int64")
orders["product_id"] = orders["product_id"].astype("int64")

customers = customers[["customer_id", "country"]].copy()
customers["country_code"] = customers["country"].astype("string").str.strip()
customers = customers.drop(columns=["country"])

products = products[["product_id", "category"]].copy()
products["category"] = products["category"].astype("string").str.strip()

merged = orders.merge(customers, on="customer_id", how="inner")
merged = merged.merge(products, on="product_id", how="inner")

valid_country = merged["country_code"].notna() & merged["country_code"].ne("")
valid_category = merged["category"].notna() & merged["category"].ne("")
merged = merged.loc[valid_country & valid_category].copy()

merged["revenue"] = (
    pd.to_numeric(merged["quantity"], errors="coerce")
    * pd.to_numeric(merged["unit_price_eur"], errors="coerce")
)

result = (
    merged.groupby(["country_code", "category"], as_index=False, dropna=True)
    .agg(
        total_revenue_eur=("revenue", "sum"),
        order_count=("order_id", "size"),
    )
    .sort_values("total_revenue_eur", ascending=False, kind="stable")
    .reset_index(drop=True)
)

Path(output_path).parent.mkdir(parents=True, exist_ok=True)
result.to_parquet(output_path, index=False)