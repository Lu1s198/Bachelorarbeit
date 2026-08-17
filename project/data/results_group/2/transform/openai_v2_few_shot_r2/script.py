import os
import pandas as pd

base_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/transform/openai_v2_few_shot_r2/output.parquet"
customers_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_hard/output.parquet"

products = pd.read_csv(os.path.join(base_path, "products_raw.csv"))
orders = pd.read_csv(os.path.join(base_path, "orders_raw.csv"))
customers = pd.read_parquet(customers_path)

products["price_eur"] = pd.to_numeric(
    products["price_eur"]
    .astype("string")
    .str.strip()
    .str.replace("€", "", regex=False)
    .str.replace("EUR", "", regex=False)
    .str.replace(",", ".", regex=False)
    .str.strip(),
    errors="coerce",
)

products["in_stock"] = (
    products["in_stock"]
    .astype("string")
    .str.strip()
    .str.lower()
    .map({"ja": True, "true": True, "1": True, "nein": False, "false": False, "0": False})
    .astype("boolean")
)

orders["total_eur"] = orders["quantity"] * orders["unit_price_eur"]
ordered_at = pd.to_datetime(orders["ordered_at"], errors="coerce")
orders["order_year"] = ordered_at.dt.year.astype("Int64")
orders["order_month"] = ordered_at.dt.month.astype("Int64")

customers["country_code"] = customers["country"].astype("string").str.strip()
products["category"] = products["category"].astype("string").str.strip()

merged = (
    orders.merge(customers[["customer_id", "country_code"]], on="customer_id", how="inner")
    .merge(products[["product_id", "category"]], on="product_id", how="inner")
)

merged = merged[
    merged["country_code"].notna()
    & merged["country_code"].ne("")
    & merged["category"].notna()
    & merged["category"].ne("")
]

result = (
    merged.groupby(["country_code", "category"], as_index=False)
    .agg(
        total_revenue_eur=("total_eur", "sum"),
        order_count=("order_id", "size"),
    )
    .sort_values("total_revenue_eur", ascending=False)
    .reset_index(drop=True)
)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)