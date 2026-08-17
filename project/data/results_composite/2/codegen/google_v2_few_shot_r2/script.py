import os
import pandas as pd

in_dir = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2"
out_file = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_composite/2/codegen/google_v2_few_shot_r2/output.parquet"

df_cust = pd.read_csv(os.path.join(in_dir, "customers_raw.csv"))
df_prod = pd.read_csv(os.path.join(in_dir, "products_raw.csv"))
df_orders = pd.read_csv(os.path.join(in_dir, "orders_raw.csv"))

for col in df_cust.select_dtypes(include="object").columns:
    df_cust[col] = df_cust[col].str.strip()

country_map = {
    "deutschland": "DE",
    "germany": "DE",
    "ger": "DE",
    "de": "DE",
    "deutshcland": "DE",
    "deutscland": "DE",
    "deu": "DE",
    "österreich": "AT",
    "oesterreich": "AT",
    "austria": "AT",
    "aut": "AT",
    "at": "AT",
    "schweiz": "CH",
    "switzerland": "CH",
    "che": "CH",
    "ch": "CH",
    "frankreich": "FR",
    "france": "FR",
    "fra": "FR",
    "fr": "FR",
    "italien": "IT",
    "italy": "IT",
    "ita": "IT",
    "it": "IT",
    "spanien": "ES",
    "spain": "ES",
    "esp": "ES",
    "es": "ES",
    "niederlande": "NL",
    "netherlands": "NL",
    "nld": "NL",
    "nl": "NL",
    "uk": "GB",
    "gb": "GB",
    "gbr": "GB",
    "united kingdom": "GB",
    "great britain": "GB",
    "grossbritannien": "GB",
    "großbritannien": "GB",
    "usa": "US",
    "us": "US",
    "united states": "US",
    "united states of america": "US",
    "polen": "PL",
    "poland": "PL",
    "pol": "PL",
    "pl": "PL",
}

df_cust["country_code"] = (
    df_cust["country"].str.lower().map(country_map).fillna("UNKNOWN")
)

df_cust = df_cust.drop_duplicates(subset=["customer_id"], keep="first")

df_prod["price_eur"] = (
    df_prod["price_eur"]
    .astype(str)
    .str.replace("EUR", "", regex=False)
    .str.replace("€", "", regex=False)
    .str.replace(",", ".", regex=False)
    .str.strip()
    .astype(float)
)

if df_prod["in_stock"].dtype == "object":
    df_prod["in_stock"] = (
        df_prod["in_stock"]
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(["true", "ja", "1", "yes", "t"])
    )
else:
    df_prod["in_stock"] = df_prod["in_stock"].astype(bool)

df_merged = df_orders.merge(df_cust, on="customer_id", how="left").merge(
    df_prod, on="product_id", how="left"
)

df_merged["country_code"] = df_merged["country_code"].fillna("UNKNOWN")
df_merged["category"] = df_merged["category"].fillna("UNKNOWN")

df_merged["revenue"] = df_merged["quantity"] * df_merged["unit_price_eur"]

result = df_merged.groupby(
    ["country_code", "category"], as_index=False
).agg(total_revenue_eur=("revenue", "sum"), order_count=("revenue", "count"))

result["total_revenue_eur"] = result["total_revenue_eur"].round(2)
result = result.sort_values(by="total_revenue_eur", ascending=False)

os.makedirs(os.path.dirname(out_file), exist_ok=True)
result.to_parquet(out_file, index=False)