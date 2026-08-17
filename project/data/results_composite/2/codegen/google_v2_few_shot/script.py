import os
import pandas as pd

input_dir = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_composite/2/codegen/google_v2_few_shot/output.parquet"

customers = pd.read_csv(f"{input_dir}/customers_raw.csv")
products = pd.read_csv(f"{input_dir}/products_raw.csv")
orders = pd.read_csv(f"{input_dir}/orders_raw.csv")

for col in customers.select_dtypes(include="object").columns:
    customers[col] = customers[col].str.strip()


def map_country(val):
    if pd.isna(val) or not str(val).strip():
        return "UNKNOWN"
    s = str(val).strip().lower()
    mapping = {
        "de": "DE",
        "germany": "DE",
        "deutschland": "DE",
        "ger": "DE",
        "deutshcland": "DE",
        "at": "AT",
        "austria": "AT",
        "österreich": "AT",
        "oesterreich": "AT",
        "aut": "AT",
        "ch": "CH",
        "switzerland": "CH",
        "schweiz": "CH",
        "suisse": "CH",
        "che": "CH",
        "fr": "FR",
        "france": "FR",
        "frankreich": "FR",
        "fra": "FR",
        "gb": "GB",
        "uk": "GB",
        "united kingdom": "GB",
        "great britain": "GB",
        "gbr": "GB",
        "england": "GB",
        "us": "US",
        "usa": "US",
        "united states": "US",
        "united states of america": "US",
        "it": "IT",
        "italy": "IT",
        "italien": "IT",
        "ita": "IT",
        "es": "ES",
        "spain": "ES",
        "spanien": "ES",
        "esp": "ES",
        "nl": "NL",
        "netherlands": "NL",
        "niederlande": "NL",
        "nld": "NL",
    }
    if s in mapping:
        return mapping[s]
    if "deut" in s or "germ" in s:
        return "DE"
    if "öster" in s or "oester" in s or "austr" in s:
        return "AT"
    if "schweiz" in s or "switz" in s or "suiss" in s:
        return "CH"
    if "frank" in s or "franc" in s:
        return "FR"
    if "span" in s or "spai" in s:
        return "ES"
    if "ital" in s:
        return "IT"
    if "nieder" in s or "nether" in s:
        return "NL"
    if "kingd" in s or "brit" in s or "engl" in s:
        return "GB"
    if "stat" in s or "americ" in s:
        return "US"
    if len(s) == 2 and s.isalpha():
        return s.upper()
    return "UNKNOWN"


customers["country_code"] = customers["country"].apply(map_country)

customers = customers.drop_duplicates(subset=["customer_id"], keep="first")

products["price_eur"] = (
    products["price_eur"]
    .astype(str)
    .str.replace("EUR", "", regex=False)
    .str.replace("€", "", regex=False)
    .str.replace(",", ".", regex=False)
    .str.strip()
    .astype(float)
)

products["in_stock"] = (
    products["in_stock"]
    .astype(str)
    .str.strip()
    .str.lower()
    .isin(["true", "ja", "yes", "1", "t", "wahr"])
)

merged = orders.merge(customers, on="customer_id", how="left").merge(
    products, on="product_id", how="left"
)

merged["country_code"] = merged["country_code"].fillna("UNKNOWN")
merged["category"] = merged["category"].fillna("UNKNOWN")
merged["revenue"] = merged["quantity"] * merged["unit_price_eur"]

aggregated = (
    merged.groupby(["country_code", "category"], as_index=False)
    .agg(
        total_revenue_eur=("revenue", lambda x: round(x.sum(), 2)),
        order_count=("order_id", "count"),
    )
    .sort_values(by="total_revenue_eur", ascending=False)
)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
aggregated.to_parquet(output_path, index=False)