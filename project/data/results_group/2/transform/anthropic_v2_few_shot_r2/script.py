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

products["in_stock"] = (
    products["in_stock"]
    .astype(str)
    .str.strip()
    .str.lower()
    .map({"ja": True, "nein": False, "true": True, "false": False, "1": True, "0": False})
)

# Step 2
orders["total_eur"] = orders["quantity"] * orders["unit_price_eur"]

ordered_at_dt = pd.to_datetime(orders["ordered_at"], errors="coerce")
orders["order_year"] = ordered_at_dt.dt.year.astype("Int64")
orders["order_month"] = ordered_at_dt.dt.month.astype("Int64")

# Step 3
merged = orders.merge(customers, on="customer_id", how="inner")
merged = merged.merge(products, on="product_id", how="inner")

merged["country_code"] = merged["country"]

merged = merged.dropna(subset=["country_code", "category"])
merged = merged[(merged["country_code"].astype(str).str.strip() != "") & (merged["category"].astype(str).str.strip() != "")]

merged["revenue"] = merged["quantity"] * merged["unit_price_eur"]

result = (
    merged.groupby(["country_code", "category"], as_index=False)
    .agg(total_revenue_eur=("revenue", "sum"), order_count=("order_id", "count"))
)

result = result.sort_values("total_revenue_eur", ascending=False).reset_index(drop=True)

result.to_parquet(
    "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/transform/anthropic_v2_few_shot_r2/output.parquet",
    index=False,
)