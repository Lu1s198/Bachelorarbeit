import os
import pandas as pd

customers_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_hard/output.parquet"
products_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/products/output.parquet"
orders_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/orders/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_isolated_r5/final/output.parquet"

customers = pd.read_parquet(customers_path)
products = pd.read_parquet(products_path)
orders = pd.read_parquet(orders_path)

orders["customer_id"] = orders["customer_id"].astype("int64")
customers["customer_id"] = customers["customer_id"].astype("int64")
orders["product_id"] = orders["product_id"].astype("int64")
products["product_id"] = products["product_id"].astype("int64")

df = orders.merge(customers[["customer_id", "country"]], on="customer_id", how="inner")
df = df.merge(products[["product_id", "category"]], on="product_id", how="inner")

df["country_code"] = df["country"]
df["line_revenue"] = df["quantity"] * df["unit_price_eur"]

df = df[
    df["country_code"].notna()
    & (df["country_code"].astype(str).str.strip() != "")
    & (df["country_code"].astype(str).str.lower() != "none")
    & (df["country_code"].astype(str).str.lower() != "nan")
]

df = df[
    df["category"].notna()
    & (df["category"].astype(str).str.strip() != "")
    & (df["category"].astype(str).str.lower() != "none")
    & (df["category"].astype(str).str.lower() != "nan")
]

agg_df = df.groupby(["country_code", "category"], as_index=False).agg(
    total_revenue_eur=("line_revenue", "sum"),
    order_count=("order_id", "count")
)

agg_df = agg_df.sort_values(by="total_revenue_eur", ascending=False).reset_index(drop=True)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
agg_df.to_parquet(output_path, index=False)