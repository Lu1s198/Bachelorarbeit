import os
import pandas as pd

products_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv"
orders_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/orders_raw.csv"
customers_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_hard/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/transform/google_v2_few_shot_r2/output.parquet"

products = pd.read_csv(products_path)
orders = pd.read_csv(orders_path)
customers = pd.read_parquet(customers_path)

products["price_eur"] = (
    products["price_eur"]
    .astype(str)
    .str.replace("€", "", regex=False)
    .str.replace("EUR", "", regex=False)
    .str.replace(",", ".", regex=False)
    .str.strip()
    .astype(float)
)

in_stock_clean = products["in_stock"].astype(str).str.strip().str.lower()
products["in_stock"] = in_stock_clean.isin(["ja", "true", "1"])

orders["total_eur"] = orders["quantity"] * orders["unit_price_eur"]
ordered_at_dt = pd.to_datetime(orders["ordered_at"])
orders["order_year"] = ordered_at_dt.dt.year
orders["order_month"] = ordered_at_dt.dt.month

merged = orders.merge(customers, on="customer_id", how="inner").merge(
    products, on="product_id", how="inner"
)

merged = merged.rename(columns={"country": "country_code"})

merged = merged.dropna(subset=["country_code", "category"])
merged = merged[
    (merged["country_code"].astype(str).str.strip() != "")
    & (merged["category"].astype(str).str.strip() != "")
]

result = (
    merged.groupby(["country_code", "category"], as_index=False)
    .agg(
        total_revenue_eur=("total_eur", "sum"),
        order_count=("order_id", "count"),
    )
    .sort_values(by="total_revenue_eur", ascending=False)
)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)