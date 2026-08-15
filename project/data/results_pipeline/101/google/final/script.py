import os
import pandas as pd

cust_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/google/dedup_hard/output.parquet"
prod_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/google/products/output.parquet"
ord_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/google/orders/output.parquet"
out_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/google/final/output.parquet"

customers = pd.read_parquet(cust_path)
products = pd.read_parquet(prod_path)
orders = pd.read_parquet(ord_path)

customers["customer_id"] = customers["customer_id"].astype("int64")
products["product_id"] = products["product_id"].astype("int64")
orders["customer_id"] = orders["customer_id"].astype("int64")
orders["product_id"] = orders["product_id"].astype("int64")

df = orders.merge(customers, on="customer_id", how="inner").merge(
    products, on="product_id", how="inner"
)

df["country_code"] = df["country"]
df["line_revenue"] = df["quantity"] * df["unit_price_eur"]

df = df[
    df["country_code"].notna()
    & (df["country_code"].astype(str).str.strip() != "")
]
df = df[
    df["category"].notna() & (df["category"].astype(str).str.strip() != "")
]

result = (
    df.groupby(["country_code", "category"], as_index=False)
    .agg(
        total_revenue_eur=("line_revenue", "sum"),
        order_count=("order_id", "count"),
    )
    .sort_values(by="total_revenue_eur", ascending=False)
    .reset_index(drop=True)
)

os.makedirs(os.path.dirname(out_path), exist_ok=True)
result.to_parquet(out_path, index=False)