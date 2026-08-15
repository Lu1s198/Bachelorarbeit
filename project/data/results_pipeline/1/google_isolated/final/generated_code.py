import os
import pandas as pd

cust_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/_reference/dedup_hard/output.parquet"
prod_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/_reference/products/output.parquet"
ord_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/_reference/orders/output.parquet"
out_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google_isolated/final/output.parquet"

customers = pd.read_parquet(cust_path)
products = pd.read_parquet(prod_path)
orders = pd.read_parquet(ord_path)

orders["customer_id"] = orders["customer_id"].astype("int64")
customers["customer_id"] = customers["customer_id"].astype("int64")

orders["product_id"] = orders["product_id"].astype("int64")
products["product_id"] = products["product_id"].astype("int64")

df = orders.merge(customers[["customer_id", "country"]], on="customer_id", how="inner")
df = df.merge(products[["product_id", "category"]], on="product_id", how="inner")

df = df.rename(columns={"country": "country_code"})

df = df.dropna(subset=["country_code", "category"])
df = df[(df["country_code"] != "") & (df["category"] != "")]

df["revenue"] = df["quantity"] * df["unit_price_eur"]

result = (
    df.groupby(["country_code", "category"], as_index=False)
    .agg(
        total_revenue_eur=("revenue", "sum"),
        order_count=("order_id", "count")
    )
    .sort_values(by="total_revenue_eur", ascending=False)
)

os.makedirs(os.path.dirname(out_path), exist_ok=True)
result.to_parquet(out_path, index=False)