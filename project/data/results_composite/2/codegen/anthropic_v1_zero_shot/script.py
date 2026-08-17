import pandas as pd
import numpy as np
import re
import unicodedata
from difflib import get_close_matches

base_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_composite/2/codegen/anthropic_v1_zero_shot/output.parquet"

customers = pd.read_csv(f"{base_path}/customers_raw.csv")
products = pd.read_csv(f"{base_path}/products_raw.csv")
orders = pd.read_csv(f"{base_path}/orders_raw.csv")

# 1. Strip whitespace from text columns in customers
for col in customers.select_dtypes(include="object").columns:
    customers[col] = customers[col].str.strip()

# 2. Normalize country to ISO alpha-2 code
country_map = {
    "germany": "DE", "deutschland": "DE", "ger": "DE", "de": "DE",
    "deutshcland": "DE", "allemagne": "DE", "germny": "DE", "deutschlnad": "DE",
    "france": "FR", "fr": "FR", "frankreich": "FR",
    "italy": "IT", "italien": "IT", "it": "IT", "italia": "IT",
    "spain": "ES", "spanien": "ES", "es": "ES", "espana": "ES",
    "netherlands": "NL", "niederlande": "NL", "nl": "NL", "holland": "NL",
    "austria": "AT", "oesterreich": "AT", "at": "AT",
    "switzerland": "CH", "schweiz": "CH", "ch": "CH", "suisse": "CH",
    "poland": "PL", "polen": "PL", "pl": "PL",
    "belgium": "BE", "belgien": "BE", "be": "BE",
    "united kingdom": "GB", "uk": "GB", "grossbritannien": "GB", "gb": "GB",
    "england": "GB", "great britain": "GB",
    "portugal": "PT", "pt": "PT",
    "sweden": "SE", "schweden": "SE", "se": "SE",
    "denmark": "DK", "daenemark": "DK", "dk": "DK",
    "norway": "NO", "norwegen": "NO", "no": "NO",
    "finland": "FI", "finnland": "FI", "fi": "FI",
    "ireland": "IE", "irland": "IE", "ie": "IE",
    "czech republic": "CZ", "tschechien": "CZ", "cz": "CZ",
    "hungary": "HU", "ungarn": "HU", "hu": "HU",
    "usa": "US", "united states": "US", "us": "US",
    "vereinigte staaten": "US", "united states of america": "US",
}


def normalize_text(val):
    if pd.isna(val):
        return ""
    val = str(val).strip().lower()
    val = unicodedata.normalize("NFKD", val)
    val = "".join(c for c in val if not unicodedata.combining(c))
    val = re.sub(r"[^a-z\s]", "", val)
    val = re.sub(r"\s+", " ", val).strip()
    return val


def map_country(val):
    norm = normalize_text(val)
    if not norm:
        return "UNKNOWN"
    if norm in country_map:
        return country_map[norm]
    matches = get_close_matches(norm, country_map.keys(), n=1, cutoff=0.8)
    if matches:
        return country_map[matches[0]]
    return "UNKNOWN"


customers["country_code"] = customers["country"].apply(map_country)

# 3. Remove duplicate customer_id, keep first occurrence
customers = customers.drop_duplicates(subset="customer_id", keep="first")

# 4. Convert price_eur to float and in_stock to boolean
def parse_price(val):
    if pd.isna(val):
        return np.nan
    s = str(val)
    s = s.upper().replace("EUR", "").strip()
    s = s.replace(".", "").replace(",", ".") if "," in s and "." in s else s.replace(",", ".")
    match = re.search(r"[-+]?\d*\.?\d+", s)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return np.nan
    return np.nan


products["price_eur"] = products["price_eur"].apply(parse_price)


def parse_bool(val):
    if pd.isna(val):
        return False
    s = str(val).strip().lower()
    true_vals = {"true", "1", "yes", "ja", "wahr", "y", "t"}
    false_vals = {"false", "0", "no", "nein", "falsch", "n", "f"}
    if s in true_vals:
        return True
    if s in false_vals:
        return False
    return False


products["in_stock"] = products["in_stock"].apply(parse_bool)

# 5. Merge orders with customers and products, keep all order rows
merged = orders.merge(
    customers[["customer_id", "country_code"]], on="customer_id", how="left"
).merge(
    products[["product_id", "category"]], on="product_id", how="left"
)

merged["country_code"] = merged["country_code"].fillna("UNKNOWN")

# 6. Aggregate revenue per country and category
merged["quantity"] = pd.to_numeric(merged["quantity"], errors="coerce")
merged["unit_price_eur"] = pd.to_numeric(merged["unit_price_eur"], errors="coerce")
merged["line_revenue"] = merged["quantity"] * merged["unit_price_eur"]

result = (
    merged.groupby(["country_code", "category"], dropna=False)
    .agg(
        total_revenue_eur=("line_revenue", "sum"),
        order_count=("line_revenue", "count"),
    )
    .reset_index()
)

result["total_revenue_eur"] = result["total_revenue_eur"].round(2)

result = result.sort_values("total_revenue_eur", ascending=False).reset_index(drop=True)

result.to_parquet(output_path, index=False)