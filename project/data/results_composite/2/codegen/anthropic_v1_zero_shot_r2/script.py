import pandas as pd
import numpy as np
import re
import difflib

base_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_composite/2/codegen/anthropic_v1_zero_shot_r2/output.parquet"

# --- Load raw data ---
customers = pd.read_csv(f"{base_path}/customers_raw.csv", dtype=str)
products = pd.read_csv(f"{base_path}/products_raw.csv", dtype=str)
orders = pd.read_csv(f"{base_path}/orders_raw.csv", dtype=str)

# --- Step 1: Trim whitespace from all text columns in customers ---
for col in customers.columns:
    if customers[col].dtype == object:
        customers[col] = customers[col].str.strip()

# --- Step 2: Normalize country to ISO-3166-1 alpha-2 ---
country_map = {
    "de": "DE", "deu": "DE", "ger": "DE", "germany": "DE", "deutschland": "DE",
    "allemagne": "DE", "germania": "DE", "alemania": "DE",

    "fr": "FR", "fra": "FR", "france": "FR", "frankreich": "FR", "francia": "FR",

    "es": "ES", "esp": "ES", "spain": "ES", "spanien": "ES", "espana": "ES",
    "espagne": "ES", "spagna": "ES",

    "it": "IT", "ita": "IT", "italy": "IT", "italien": "IT", "italia": "IT",
    "italie": "IT",

    "at": "AT", "aut": "AT", "austria": "AT", "oesterreich": "AT",
    "österreich": "AT", "autriche": "AT",

    "ch": "CH", "che": "CH", "switzerland": "CH", "schweiz": "CH",
    "suisse": "CH", "svizzera": "CH",

    "nl": "NL", "nld": "NL", "netherlands": "NL", "niederlande": "NL",
    "pays-bas": "NL", "paysbas": "NL", "olanda": "NL", "holland": "NL",

    "be": "BE", "bel": "BE", "belgium": "BE", "belgien": "BE",
    "belgique": "BE", "belgio": "BE",

    "pl": "PL", "pol": "PL", "poland": "PL", "polen": "PL", "pologne": "PL",
    "polonia": "PL",

    "gb": "GB", "gbr": "GB", "uk": "GB", "united kingdom": "GB",
    "england": "GB", "grossbritannien": "GB", "großbritannien": "GB",
    "royaume-uni": "GB", "regno unito": "GB",

    "us": "US", "usa": "US", "united states": "US", "united states of america": "US",
    "vereinigte staaten": "US", "etats-unis": "US", "stati uniti": "US",

    "pt": "PT", "prt": "PT", "portugal": "PT", "portogallo": "PT",

    "dk": "DK", "dnk": "DK", "denmark": "DK", "daenemark": "DK", "dänemark": "DK",
    "danemark": "DK", "danimarca": "DK",

    "se": "SE", "swe": "SE", "sweden": "SE", "schweden": "SE", "suede": "SE",
    "svezia": "SE",

    "no": "NO", "nor": "NO", "norway": "NO", "norwegen": "NO", "norvege": "NO",
    "norvegia": "NO",

    "fi": "FI", "fin": "FI", "finland": "FI", "finnland": "FI", "finlande": "FI",
    "finlandia": "FI",

    "cz": "CZ", "cze": "CZ", "czech republic": "CZ", "tschechien": "CZ",
    "republique tcheque": "CZ", "repubblica ceca": "CZ",

    "ie": "IE", "irl": "IE", "ireland": "IE", "irland": "IE", "irlande": "IE",
    "irlanda": "IE",

    "lu": "LU", "lux": "LU", "luxembourg": "LU", "luxemburg": "LU",
    "lussemburgo": "LU",

    "hu": "HU", "hun": "HU", "hungary": "HU", "ungarn": "HU", "hongrie": "HU",
    "ungheria": "HU",
}

known_keys = list(country_map.keys())

def normalize_country(value):
    if pd.isna(value) or str(value).strip() == "":
        return "UNKNOWN"
    v = str(value).strip().lower()
    v = re.sub(r"[.\-_]", " ", v)
    v = re.sub(r"\s+", " ", v).strip()
    if v in country_map:
        return country_map[v]
    # try close match for typos
    matches = difflib.get_close_matches(v, known_keys, n=1, cutoff=0.82)
    if matches:
        return country_map[matches[0]]
    return "UNKNOWN"

if "country" in customers.columns:
    customers["country_code"] = customers["country"].apply(normalize_country)
else:
    customers["country_code"] = "UNKNOWN"

# --- Step 3: Deduplicate customer_id, keep first occurrence ---
customers = customers.drop_duplicates(subset=["customer_id"], keep="first")

# --- Step 4: Convert products price_eur to float and in_stock to bool ---
def parse_price(value):
    if pd.isna(value):
        return np.nan
    s = str(value).strip()
    s = re.sub(r"[^\d,.\-]", "", s)
    s = s.strip()
    if s == "":
        return np.nan
    # If both comma and dot present, assume comma is thousands sep, dot decimal
    if "," in s and "." in s:
        s = s.replace(",", "")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return np.nan

products["price_eur"] = products["price_eur"].apply(parse_price)

def parse_bool(value):
    if pd.isna(value):
        return False
    s = str(value).strip().lower()
    return s in ("true", "1", "yes", "ja", "y", "wahr", "in stock", "instock")

products["in_stock"] = products["in_stock"].apply(parse_bool)

# --- Step 5: Merge orders with customers and products ---
orders["quantity"] = pd.to_numeric(orders["quantity"], errors="coerce")
orders["unit_price_eur"] = orders["unit_price_eur"].apply(parse_price)

merged = orders.merge(
    customers[["customer_id", "country_code"]],
    on="customer_id",
    how="left"
)

merged = merged.merge(
    products[["product_id", "category"]],
    on="product_id",
    how="left"
)

merged["country_code"] = merged["country_code"].fillna("UNKNOWN")
merged["category"] = merged["category"].fillna("UNKNOWN")

# --- Step 6: Aggregate revenue per country and category ---
merged["line_revenue"] = merged["quantity"] * merged["unit_price_eur"]

agg = merged.groupby(["country_code", "category"], as_index=False).agg(
    total_revenue_eur=("line_revenue", "sum"),
    order_count=("line_revenue", "count")
)

agg["total_revenue_eur"] = agg["total_revenue_eur"].round(2)

agg = agg.sort_values("total_revenue_eur", ascending=False).reset_index(drop=True)

# --- Write output ---
agg.to_parquet(output_path, index=False)