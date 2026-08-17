import pandas as pd

base = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2"
out_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_composite/2/codegen/anthropic_v2_few_shot_r2/output.parquet"

customers = pd.read_csv(f"{base}/customers_raw.csv")
products = pd.read_csv(f"{base}/products_raw.csv")
orders = pd.read_csv(f"{base}/orders_raw.csv")

# 1. Trim whitespace in all text columns of customers
for col in customers.select_dtypes(include="object").columns:
    customers[col] = customers[col].str.strip()

# 2. Normalize country to ISO-3166-1 alpha-2 code
country_map = {
    "de": "DE", "deu": "DE", "ger": "DE", "germany": "DE", "deutschland": "DE",
    "deutshcland": "DE", "allemagne": "DE", "germani": "DE", "germay": "DE",
    "at": "AT", "aut": "AT", "austria": "AT", "oesterreich": "AT", "österreich": "AT",
    "ch": "CH", "che": "CH", "switzerland": "CH", "schweiz": "CH", "suisse": "CH",
    "fr": "FR", "fra": "FR", "france": "FR", "frankreich": "FR",
    "it": "IT", "ita": "IT", "italy": "IT", "italien": "IT", "italia": "IT",
    "es": "ES", "esp": "ES", "spain": "ES", "spanien": "ES", "espana": "ES", "españa": "ES",
    "nl": "NL", "nld": "NL", "netherlands": "NL", "niederlande": "NL", "holland": "NL",
    "gb": "GB", "uk": "GB", "united kingdom": "GB", "grossbritannien": "GB",
    "großbritannien": "GB", "england": "GB", "britain": "GB",
    "us": "US", "usa": "US", "united states": "US", "vereinigte staaten": "US",
    "america": "US",
    "pl": "PL", "pol": "PL", "poland": "PL", "polen": "PL",
    "be": "BE", "bel": "BE", "belgium": "BE", "belgien": "BE",
    "pt": "PT", "prt": "PT", "portugal": "PT",
    "dk": "DK", "dnk": "DK", "denmark": "DK", "daenemark": "DK", "dänemark": "DK",
    "se": "SE", "swe": "SE", "sweden": "SE", "schweden": "SE",
    "no": "NO", "nor": "NO", "norway": "NO", "norwegen": "NO",
    "fi": "FI", "fin": "FI", "finland": "FI", "finnland": "FI",
    "ie": "IE", "irl": "IE", "ireland": "IE", "irland": "IE",
    "lu": "LU", "lux": "LU", "luxembourg": "LU", "luxemburg": "LU",
    "cz": "CZ", "cze": "CZ", "czech republic": "CZ", "tschechien": "CZ",
}


def normalize_country(val):
    if pd.isna(val):
        return "UNKNOWN"
    key = str(val).strip().lower()
    return country_map.get(key, "UNKNOWN")


customers["country_code"] = customers["country"].apply(normalize_country)

# 3. Drop duplicate customer_id, keep first occurrence
customers = customers.drop_duplicates(subset="customer_id", keep="first")

# 4. Convert price_eur to float and in_stock to boolean
products["price_eur"] = (
    products["price_eur"]
    .astype(str)
    .str.replace("EUR", "", regex=False)
    .str.replace("€", "", regex=False)
    .str.strip()
    .str.replace(",", ".", regex=False)
    .astype(float)
)

products["in_stock"] = (
    products["in_stock"]
    .astype(str)
    .str.strip()
    .str.lower()
    .map({"true": True, "yes": True, "ja": True, "1": True,
          "false": False, "no": False, "nein": False, "0": False})
)

# 5. Merge orders with customers and products (left joins, keep all order rows)
merged = orders.merge(customers, on="customer_id", how="left")
merged = merged.merge(products, on="product_id", how="left", suffixes=("", "_product"))

# 6. Aggregate revenue and order count per country_code and category
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