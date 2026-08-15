import os
import pandas as pd

customers_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r3/dedup_hard/output.parquet"
products_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r3/products/output.parquet"
orders_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r3/orders/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r3/final/output.parquet"

customers = pd.read_parquet(customers_path)
products = pd.read_parquet(products_path)
orders = pd.read_parquet(orders_path)

customers["customer_id"] = customers["customer_id"].astype("int64")
products["product_id"] = products["product_id"].astype("int64")
orders["customer_id"] = orders["customer_id"].astype("int64")
orders["product_id"] = orders["product_id"].astype("int64")

df = orders.merge(customers, on="customer_id", how="inner")
df = df.merge(products, on="product_id", how="inner")

df["country_code"] = df["country"]

df = df[
    df["country_code"].notna()
    & df["category"].notna()
    & (df["country_code"].astype(str).str.strip() != "")
    & (df["category"].astype(str).str.strip() != "")
]

df["line_revenue"] = df["quantity"] * df["unit_price_eur"]

aggregated = (
    df.groupby(["country_code", "category"], as_index=False)
    .agg(
        total_revenue_eur=("line_revenue", "sum"),
        order_count=("order_id", "count"),
    )
    .sort_values(by="total_revenue_eur", ascending=False)
)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
aggregated.to_parquet(output_path, index=False)