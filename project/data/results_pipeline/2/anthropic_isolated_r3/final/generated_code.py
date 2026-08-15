import pandas as pd
import numpy as np

customers = pd.read_parquet("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_hard/output.parquet")
products = pd.read_parquet("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/products/output.parquet")
orders = pd.read_parquet("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/orders/output.parquet")

customers["customer_id"] = customers["customer_id"].astype("int64")
orders["customer_id"] = orders["customer_id"].astype("int64")
products["product_id"] = products["product_id"].astype("int64")
orders["product_id"] = orders["product_id"].astype("int64")

customers = customers.rename(columns={"country": "country_code"})

merged = orders.merge(customers[["customer_id", "country_code"]], on="customer_id", how="inner")
merged = merged.merge(products[["product_id", "category"]], on="product_id", how="inner")

merged = merged.dropna(subset=["country_code", "category"])
merged = merged[(merged["country_code"].astype(str).str.strip() != "") & (merged["category"].astype(str).str.strip() != "")]

merged["revenue"] = merged["quantity"] * merged["unit_price_eur"]

result = merged.groupby(["country_code", "category"], as_index=False).agg(
    total_revenue_eur=("revenue", "sum"),
    order_count=("order_id", "count")
)

result = result.sort_values("total_revenue_eur", ascending=False).reset_index(drop=True)

result.to_parquet("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_isolated_r3/final/output.parquet", index=False)