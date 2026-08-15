import os
import pandas as pd

cust_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_hard/output.parquet"
prod_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/products/output.parquet"
ord_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/orders/output.parquet"
out_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_isolated/final/output.parquet"

customers = pd.read_parquet(cust_path)
products = pd.read_parquet(prod_path)
orders = pd.read_parquet(ord_path)

customers["customer_id"] = customers["customer_id"].astype("int64")
products["product_id"] = products["product_id"].astype("int64")
orders["customer_id"] = orders["customer_id"].astype("int64")
orders["product_id"] = orders["product_id"].astype("int64")

customers = customers.rename(columns={"country": "country_code"})

df = orders.merge(customers, on="customer_id", how="inner")
df = df.merge(products, on="product_id", how="inner")

df["revenue"] = df["quantity"] * df["unit_price_eur"]

df = df.dropna(subset=["country_code", "category"])
df = df[(df["country_code"].astype(str).str.strip() != "") & (df["category"].astype(str).str.strip() != "")]

res = df.groupby(["country_code", "category"], as_index=False).agg(
    total_revenue_eur=("revenue", "sum"),
    order_count=("order_id", "count")
)

res = res.sort_values(by="total_revenue_eur", ascending=False).reset_index(drop=True)

os.makedirs(os.path.dirname(out_path), exist_ok=True)
res.to_parquet(out_path, index=False)