import os
import re
import pandas as pd

products_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv"
orders_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/orders_raw.csv"
customers_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_hard/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/transform/openai_v1_zero_shot/output.parquet"

products = pd.read_csv(products_path)
orders = pd.read_csv(orders_path)
customers = pd.read_parquet(customers_path)

def parse_eur(value):
    if pd.isna(value):
        return pd.NA
    text = str(value).strip()
    text = re.sub(r"[^\d,.\-]", "", text)

    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")

    return pd.to_numeric(text, errors="coerce")

products["price_eur"] = products["price_eur"].map(parse_eur).astype("Float64")

stock_mapping = {
    "ja": True,
    "yes": True,
    "true": True,
    "1": True,
    "nein": False,
    "no": False,
    "false": False,
    "0": False,
}
products["in_stock"] = (
    products["in_stock"]
    .astype("string")
    .str.strip()
    .str.lower()
    .map(stock_mapping)
    .astype("boolean")
)

orders["total_eur"] = (
    pd.to_numeric(orders["quantity"], errors="coerce")
    * pd.to_numeric(orders["unit_price_eur"], errors="coerce")
)

ordered_at = pd.to_datetime(orders["ordered_at"], errors="coerce")
orders["order_year"] = ordered_at.dt.year.astype("Int64")
orders["order_month"] = ordered_at.dt.month.astype("Int64")

customers = customers.copy()
customers["country_code"] = customers["country"].astype("string").str.strip()

products = products.copy()
products["category"] = products["category"].astype("string").str.strip()

merged = (
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

merged = merged[
    merged["country_code"].notna()
    & merged["category"].notna()
    & merged["country_code"].ne("")
    & merged["category"].ne("")
].copy()

result = (
    merged.groupby(["country_code", "category"], as_index=False)
    .agg(
        total_revenue_eur=("total_eur", "sum"),
        order_count=("order_id", "count"),
    )
    .sort_values("total_revenue_eur", ascending=False, kind="stable")
    .reset_index(drop=True)
)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)