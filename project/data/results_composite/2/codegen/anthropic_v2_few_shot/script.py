import pandas as pd
import difflib

base = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2"
out_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_composite/2/codegen/anthropic_v2_few_shot/output.parquet"

customers = pd.read_csv(f"{base}/customers_raw.csv")
products = pd.read_csv(f"{base}/products_raw.csv")
orders = pd.read_csv(f"{base}/orders_raw.csv")

# 1. Trim whitespace in text columns of customers
text_cols = customers.select_dtypes(include="object").columns
for col in text_cols:
    customers[col] = customers[col].str.strip()

# 2. Map country to ISO-3166-1-alpha-2 code
country_map = {
    "germany": "DE", "deutschland": "DE", "ger": "DE", "de": "DE",
    "france": "FR", "frankreich": "FR", "fra": "FR", "fr": "FR",
    "italy": "IT", "italien": "IT", "ita": "IT", "it": "IT",
    "spain": "ES", "spanien": "ES", "esp": "ES", "es": "ES",
    "united kingdom": "GB", "uk": "GB", "großbritannien": "GB",
    "grossbritannien": "GB", "gb": "GB", "great britain": "GB",
    "united states": "US", "usa": "US", "vereinigte staaten": "US", "us": "US",
    "austria": "AT", "österreich": "AT", "oesterreich": "AT", "at": "AT",
    "switzerland": "CH", "schweiz": "CH", "ch": "CH",
    "netherlands": "NL", "niederlande": "NL", "nl": "NL",
    "poland": "PL", "polen": "PL", "pl": "PL",
    "belgium": "BE", "belgien": "BE", "be": "BE",
    "portugal": "PT", "pt": "PT",
    "sweden": "SE", "schweden": "SE", "se": "SE",
    "denmark": "DK", "dänemark": "DK", "daenemark": "DK", "dk": "DK",
    "norway": "NO", "norwegen": "NO", "no": "NO",
    "finland": "FI", "finnland": "FI", "fi": "FI",
    "czech republic": "CZ", "tschechien": "CZ", "cz": "CZ",
    "ireland": "IE", "irland": "IE", "ie": "IE",
    "luxembourg": "LU", "luxemburg": "LU", "lu": "LU",
}


def map_country(value):
    if pd.isna(value) or str(value).strip() == "":
        return "UNKNOWN"
    v = str(value).strip().lower()
    if v in country_map:
        return country_map[v]
    candidates = difflib.get_close_matches(v, country_map.keys(), n=1, cutoff=0.75)
    if candidates:
        return country_map[candidates[0]]
    return "UNKNOWN"


customers["country_code"] = customers["country"].apply(map_country)

# 3. Remove duplicate customer_id, keep first occurrence
customers = customers.drop_duplicates(subset="customer_id", keep="first")

# 4. Clean products: price_eur -> float, in_stock -> bool
products["price_eur"] = (
    products["price_eur"]
    .astype(str)
    .str.replace("EUR", "", regex=False)
    .str.replace(",", ".", regex=False)
    .str.strip()
    .astype(float)
)

products["in_stock"] = (
    products["in_stock"]
    .astype(str)
    .str.strip()
    .str.lower()
    .map({"true": True, "false": False, "yes": True, "no": False,
          "ja": True, "nein": False, "1": True, "0": False})
)

# 5. Merge orders with customers and products
merged = orders.merge(customers, on="customer_id", how="left")
merged = merged.merge(products, on="product_id", how="left")

# 6. Aggregate revenue per country and category
merged["revenue"] = merged["quantity"] * merged["unit_price_eur"]

result = (
    merged.groupby(["country_code", "category"], dropna=False)
    .agg(
        total_revenue_eur=("revenue", "sum"),
        order_count=("revenue", "count"),
    )
    .reset_index()
)

result["total_revenue_eur"] = result["total_revenue_eur"].round(2)

result = result.sort_values("total_revenue_eur", ascending=False).reset_index(drop=True)

result.to_parquet(out_path, index=False)