import pandas as pd
from pathlib import Path

products_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv"
orders_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/orders_raw.csv"
customers_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_hard/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/transform/openai_v2_few_shot/output.parquet"

products = pd.read_csv(products_path)
orders = pd.read_csv(orders_path)
customers = pd.read_parquet(customers_path)

products["price_eur"] = pd.to_numeric(
    products["price_eur"]
    .astype("string")
    .str.strip()
    .str.replace("€", "", regex=False)
    .str.replace("EUR", "", regex=False)
    .str.replace("eur", "", regex=False)
    .str.strip()
    .str.replace(",", ".", regex=False),
    errors="coerce",
)

products["in_stock"] = (
    products["in_stock"]
    .astype("string")
    .str.strip()
    .str.lower()
    .map(
        {
            "ja": True,
            "true": True,
            "1": True,
            "nein": False,
            "false": False,
            "0": False,
        }
    )
    .astype("boolean")
)

orders["total_eur"] = orders["quantity"] * orders["unit_price_eur"]

ordered_at = pd.to_datetime(orders["ordered_at"], errors="coerce")
orders["order_year"] = ordered_at.dt.year.astype("Int64")
orders["order_month"] = ordered_at.dt.month.astype("Int64")

customers["country_code"] = customers["country"].astype("string").str.strip()
products["category"] = products["category"].astype("string").str.strip()

result = (
    orders.merge(
        customers[["customer_id", "country_code"]],
        on="customer_id",
        how="inner",
    )
    .merge(
        products[["product_id", "category"]],
        on="product_id",
        how="inner",
    )
)

result = result[
    result["country_code"].notna()
    & result["category"].notna()
    & result["country_code"].ne("")
    & result["category"].ne("")
]

result = (
    result.groupby(["country_code", "category"], as_index=False)
    .agg(
        total_revenue_eur=("total_eur", "sum"),
        order_count=("order_id", "count"),
    )
    .sort_values("total_revenue_eur", ascending=False, kind="stable")
)

Path(output_path).parent.mkdir(parents=True, exist_ok=True)
result.to_parquet(output_path, index=False)