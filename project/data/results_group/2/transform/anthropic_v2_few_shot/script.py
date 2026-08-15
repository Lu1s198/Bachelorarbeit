import pandas as pd

products = pd.read_csv("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv")
orders = pd.read_csv("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/orders_raw.csv")
customers = pd.read_parquet("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_hard/output.parquet")

# Step 1
products["price_eur"] = (
    products["price_eur"]
    .astype(str)
    .str.replace("€", "", regex=False)
    .str.replace("EUR", "", regex=False)
    .str.strip()
    .str.replace(",", ".", regex=False)
    .astype(float)
)

def to_bool(val):
    v = str(val).strip().lower()
    if v in ("ja", "true", "1"):
        return True
    if v in ("nein", "false", "0"):
        return False
    return None

products["in_stock"] = products["in_stock"].apply(to_bool)

# Step 2
orders["total_eur"] = orders["quantity"] * orders["unit_price_eur"]
orders["ordered_at"] = pd.to_datetime(orders["ordered_at"], errors="coerce")
orders["order_year"] = orders["ordered_at"].dt.year.astype("Int64")
orders["order_month"] = orders["ordered_at"].dt.month.astype("Int64")

# Step 3
merged = orders.merge(customers, on="customer_id", how="inner")
merged = merged.merge(products, on="product_id", how="inner")

merged["country_code"] = merged["country"]

merged = merged[
    merged["country_code"].notna() & (merged["country_code"].astype(str).str.strip() != "") &
    merged["category"].notna() & (merged["category"].astype(str).str.strip() != "")
]

result = (
    merged.groupby(["country_code", "category"])
    .agg(
        total_revenue_eur=("total_eur", "sum"),
        order_count=("order_id", "count"),
    )
    .reset_index()
    .sort_values("total_revenue_eur", ascending=False)
)

result.to_parquet(
    "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/transform/anthropic_v2_few_shot/output.parquet",
    index=False,
)