import pandas as pd

customers = pd.read_parquet(
    "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/dedup_hard/output.parquet"
)
products = pd.read_parquet(
    "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/products/output.parquet"
)
orders = pd.read_parquet(
    "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/orders/output.parquet"
)

customers["customer_id"] = customers["customer_id"].astype(str)
orders["customer_id"] = orders["customer_id"].astype(str)
products["product_id"] = products["product_id"].astype(str)
orders["product_id"] = orders["product_id"].astype(str)

merged = orders.merge(customers, on="customer_id", how="inner")
merged = merged.merge(products, on="product_id", how="inner")

merged["country_code"] = merged["country"]

merged["revenue"] = merged["quantity"] * merged["unit_price_eur"]

result = (
    merged.groupby(["country_code", "category"], as_index=False)
    .agg(
        total_revenue_eur=("revenue", "sum"),
        order_count=("revenue", "count"),
    )
    .sort_values("total_revenue_eur", ascending=False)
    .reset_index(drop=True)
)

result.to_parquet(
    "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/final/output.parquet",
    index=False,
)