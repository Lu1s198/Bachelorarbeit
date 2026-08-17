import os
import re
import unicodedata
from difflib import get_close_matches

import pandas as pd

BASE_DIR = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2"
OUTPUT_PATH = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_composite/2/codegen/openai_v1_zero_shot/output.parquet"

customers_path = os.path.join(BASE_DIR, "customers_raw.csv")
products_path = os.path.join(BASE_DIR, "products_raw.csv")
orders_path = os.path.join(BASE_DIR, "orders_raw.csv")

customers = pd.read_csv(customers_path)
products = pd.read_csv(products_path)
orders = pd.read_csv(orders_path)

for column in customers.columns:
    if pd.api.types.is_object_dtype(customers[column]) or pd.api.types.is_string_dtype(customers[column]):
        customers[column] = customers[column].astype("string").str.strip()

def normalize_country(value):
    if pd.isna(value):
        return ""
    value = str(value).strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = re.sub(r"[^a-z]", "", value)
    return value

country_aliases = {
    "DE": [
        "de", "deu", "ger", "deutschland", "deutshcland", "germany",
        "allemagne", "alemania", "germania", "tedesco", "deutsch"
    ],
    "AT": ["at", "aut", "austria", "osterreich", "oesterreich", "autriche"],
    "CH": ["ch", "che", "schweiz", "switzerland", "suisse", "svizzera", "suiza"],
    "FR": ["fr", "fra", "fre", "france", "frankreich", "francais"],
    "IT": ["it", "ita", "italy", "italien", "italia"],
    "ES": ["es", "esp", "spain", "spanien", "espana", "espagne"],
    "PT": ["pt", "prt", "portugal", "portugalia"],
    "NL": ["nl", "nld", "netherlands", "holland", "niederlande", "paysbas"],
    "BE": ["be", "bel", "belgium", "belgien", "belgique", "belgie"],
    "LU": ["lu", "lux", "luxembourg", "luxemburg"],
    "GB": [
        "gb", "uk", "gbr", "unitedkingdom", "greatbritain", "britain",
        "england", "grossbritannien", "vereinigteskonigreich"
    ],
    "IE": ["ie", "irl", "ireland", "irland"],
    "US": [
        "us", "usa", "unitedstates", "unitedstatesofamerica", "america",
        "vereinigtestaaten", "vereinigtestaatenvonamerika"
    ],
    "CA": ["ca", "can", "canada", "kanada"],
    "AU": ["au", "aus", "australia", "australien"],
    "NZ": ["nz", "nzl", "newzealand", "neuseeland"],
    "SE": ["se", "swe", "sweden", "schweden", "suede"],
    "NO": ["no", "nor", "norway", "norwegen", "norge"],
    "DK": ["dk", "dnk", "denmark", "danemark", "dania"],
    "FI": ["fi", "fin", "finland", "finnland", "suomi"],
    "PL": ["pl", "pol", "poland", "polen", "polska"],
    "CZ": ["cz", "cze", "czechia", "czechrepublic", "tschechien"],
    "SK": ["sk", "svk", "slovakia", "slowakei"],
    "HU": ["hu", "hun", "hungary", "ungarn"],
    "RO": ["ro", "rou", "romania", "rumanien"],
    "BG": ["bg", "bgr", "bulgaria", "bulgarien"],
    "GR": ["gr", "greece", "griechenland", "hellas"],
    "TR": ["tr", "tur", "turkey", "turkiye", "tuerkei", "turkei"],
    "RU": ["ru", "rus", "russia", "russland"],
    "UA": ["ua", "ukr", "ukraine"],
    "CN": ["cn", "chn", "china", "vrchina"],
    "JP": ["jp", "jpn", "japan", "japon"],
    "KR": ["kr", "kor", "southkorea", "korea", "sudkorea"],
    "IN": ["in", "ind", "india", "indien"],
    "BR": ["br", "bra", "brazil", "brasil", "brasilien"],
    "MX": ["mx", "mex", "mexico", "mexiko"],
    "AR": ["ar", "arg", "argentina", "argentinen"],
    "ZA": ["za", "zaf", "southafrica", "southafrica", "sudafrika"],
    "AE": ["ae", "are", "unitedarabemirates", "uae", "vereinigtearabischeemirate"],
    "SA": ["sa", "sau", "saudiarabia", "saudiarabien"],
    "IL": ["il", "isr", "israel"],
}

alias_to_code = {}
for code, aliases in country_aliases.items():
    for alias in aliases:
        normalized_alias = normalize_country(alias)
        if normalized_alias not in alias_to_code:
            alias_to_code[normalized_alias] = code

all_aliases = list(alias_to_code.keys())

def resolve_country(value):
    normalized = normalize_country(value)
    if not normalized:
        return "UNKNOWN"
    if normalized in alias_to_code:
        return alias_to_code[normalized]

    matches = get_close_matches(normalized, all_aliases, n=3, cutoff=0.86)
    if len(matches) == 1:
        return alias_to_code[matches[0]]
    if len(matches) > 1:
        matched_codes = {alias_to_code[match] for match in matches}
        if len(matched_codes) == 1:
            return matched_codes.pop()
    return "UNKNOWN"

if "country" in customers.columns:
    customers["country_code"] = customers["country"].apply(resolve_country)
else:
    customers["country_code"] = "UNKNOWN"

customers = customers.drop_duplicates(subset=["customer_id"], keep="first")

def parse_numeric(value):
    if pd.isna(value):
        return float("nan")
    text = str(value).strip()
    if not text:
        return float("nan")

    text = re.sub(r"[^\d,.\-+]", "", text)

    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        if text.count(",") == 1:
            text = text.replace(",", ".")
        else:
            text = text.replace(",", "")

    return pd.to_numeric(text, errors="coerce")

def parse_boolean(value):
    if pd.isna(value):
        return pd.NA
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes", "y", "ja", "j", "in stock", "available", "verfuegbar", "verfügbar"}:
        return True
    if normalized in {"false", "0", "no", "n", "nein", "out of stock", "unavailable", "nicht verfuegbar", "nicht verfügbar"}:
        return False
    return pd.NA

products["price_eur"] = products["price_eur"].apply(parse_numeric).astype(float)
products["in_stock"] = products["in_stock"].apply(parse_boolean).astype("boolean")

orders["quantity"] = orders["quantity"].apply(parse_numeric)
orders["unit_price_eur"] = orders["unit_price_eur"].apply(parse_numeric)

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
merged["total_revenue_eur"] = merged["quantity"] * merged["unit_price_eur"]

group_columns = ["country_code", "category"]

if "order_id" in merged.columns:
    result = (
        merged.groupby(group_columns, dropna=False)
        .agg(
            total_revenue_eur=("total_revenue_eur", "sum"),
            order_count=("order_id", "nunique")
        )
        .reset_index()
    )
else:
    result = (
        merged.groupby(group_columns, dropna=False)
        .agg(
            total_revenue_eur=("total_revenue_eur", "sum"),
            order_count=("total_revenue_eur", "size")
        )
        .reset_index()
    )

result["total_revenue_eur"] = result["total_revenue_eur"].round(2)
result = result.sort_values(
    by="total_revenue_eur",
    ascending=False,
    kind="mergesort"
).reset_index(drop=True)

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
result.to_parquet(OUTPUT_PATH, index=False)