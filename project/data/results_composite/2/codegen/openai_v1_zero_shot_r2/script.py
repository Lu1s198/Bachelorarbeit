import re
import unicodedata
from difflib import get_close_matches
from pathlib import Path

import pandas as pd


BASE_DIR = Path(r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2")
OUTPUT_PATH = Path(
    r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_composite/2/codegen/openai_v1_zero_shot_r2/output.parquet"
)


def read_csv_robust(path):
    return pd.read_csv(path, sep=None, engine="python")


def normalize_text(value):
    if pd.isna(value):
        return ""
    value = str(value).strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]", "", value)


COUNTRY_ALIASES = {
    "DE": [
        "de", "deu", "ger", "germany", "deutschland", "deutshcland",
        "deutschlad", "deutchland", "alemania", "allemagne", "germania",
    ],
    "AT": ["at", "aut", "austria", "osterreich", "österreich", "austria"],
    "CH": ["ch", "che", "switzerland", "schweiz", "suisse", "svizzera", "helvetia"],
    "FR": ["fr", "fra", "fre", "france", "frankreich", "francia"],
    "IT": ["it", "ita", "italy", "italien", "italia"],
    "ES": ["es", "esp", "spain", "spanien", "espana", "españa"],
    "PT": ["pt", "prt", "portugal"],
    "NL": ["nl", "nld", "netherlands", "holland", "niederlande", "paysbas"],
    "BE": ["be", "bel", "belgium", "belgien", "belgique"],
    "LU": ["lu", "lux", "luxembourg", "luxemburg"],
    "GB": [
        "gb", "gbr", "uk", "u.k.", "unitedkingdom", "greatbritain",
        "england", "britannien", "grossbritannien", "großbritannien",
    ],
    "IE": ["ie", "irl", "ireland", "irland"],
    "US": [
        "us", "usa", "u.s.", "u.s.a.", "unitedstates", "unitedstatesofamerica",
        "america", "amerika", "vereinigtestaaten",
    ],
    "CA": ["ca", "can", "canada", "kanada"],
    "MX": ["mx", "mex", "mexico", "méxico"],
    "BR": ["br", "bra", "brazil", "brasil", "brasilien"],
    "AR": ["ar", "arg", "argentina", "argentinien"],
    "CL": ["cl", "chl", "chile"],
    "CO": ["co", "col", "colombia", "kolumbien"],
    "AU": ["au", "aus", "australia", "australien"],
    "NZ": ["nz", "nzl", "newzealand", "neuseeland"],
    "JP": ["jp", "jpn", "japan", "japon"],
    "CN": ["cn", "chn", "china", "china", "vrchina"],
    "KR": ["kr", "kor", "southkorea", "korea", "sudkorea", "republicofkorea"],
    "IN": ["in", "ind", "india", "indien"],
    "SG": ["sg", "sgp", "singapore", "singapur"],
    "HK": ["hk", "hkg", "hongkong"],
    "AE": ["ae", "are", "uae", "unitedarabemirates", "vereinigtearabischeemirate"],
    "SA": ["sa", "sau", "saudiarabia", "saudiarabien"],
    "TR": ["tr", "tur", "turkey", "türkiye", "turkiye", "tuerkei", "turkei"],
    "PL": ["pl", "pol", "poland", "polen", "polska"],
    "CZ": ["cz", "cze", "czechia", "czechrepublic", "tschechien"],
    "DK": ["dk", "dnk", "denmark", "dänemark", "daenemark"],
    "SE": ["se", "swe", "sweden", "schweden"],
    "NO": ["no", "nor", "norway", "norwegen"],
    "FI": ["fi", "fin", "finland", "finnland"],
    "RO": ["ro", "rou", "romania", "rumänien", "rumanien"],
    "HU": ["hu", "hun", "hungary", "ungarn"],
    "GR": ["gr", "grc", "greece", "griechenland", "hellas"],
    "RU": ["ru", "rus", "russia", "russland"],
    "UA": ["ua", "ukr", "ukraine", "ukraine"],
    "ZA": ["za", "zaf", "southafrica", "southafrica", "sudafrika"],
    "EG": ["eg", "egy", "egypt", "ägypten", "aegypten"],
    "IL": ["il", "isr", "israel"],
}

COUNTRY_LOOKUP = {}
for code, aliases in COUNTRY_ALIASES.items():
    for alias in aliases:
        COUNTRY_LOOKUP[normalize_text(alias)] = code

COUNTRY_KEYS = list(COUNTRY_LOOKUP.keys())


def country_to_code(value):
    key = normalize_text(value)
    if not key:
        return "UNKNOWN"
    if key in COUNTRY_LOOKUP:
        return COUNTRY_LOOKUP[key]

    candidates = get_close_matches(key, COUNTRY_KEYS, n=2, cutoff=0.84)
    if len(candidates) == 1:
        return COUNTRY_LOOKUP[candidates[0]]
    if len(candidates) == 2:
        first_code = COUNTRY_LOOKUP[candidates[0]]
        second_code = COUNTRY_LOOKUP[candidates[1]]
        if first_code == second_code:
            return first_code
    return "UNKNOWN"


def parse_number(value):
    if pd.isna(value):
        return float("nan")

    text = str(value).strip()
    if not text:
        return float("nan")

    text = re.sub(r"[^0-9,.\-+]", "", text)
    if not re.search(r"\d", text):
        return float("nan")

    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        if text.count(",") > 1:
            parts = text.split(",")
            if len(parts[-1]) in (1, 2):
                text = "".join(parts[:-1]).replace(",", "") + "." + parts[-1]
            else:
                text = text.replace(",", "")
        else:
            text = text.replace(",", ".")
    elif text.count(".") > 1:
        parts = text.split(".")
        if len(parts[-1]) in (1, 2):
            text = "".join(parts[:-1]) + "." + parts[-1]
        else:
            text = text.replace(".", "")

    return pd.to_numeric(text, errors="coerce")


def parse_boolean(value):
    if pd.isna(value):
        return pd.NA

    normalized = normalize_text(value)
    true_values = {"true", "1", "yes", "y", "ja", "j", "available", "instock", "inlager"}
    false_values = {"false", "0", "no", "n", "nein", "notavailable", "outofstock", "nichtauf lager"}

    if normalized in true_values:
        return True
    if normalized in false_values:
        return False
    return pd.NA


customers = read_csv_robust(BASE_DIR / "customers_raw.csv")
products = read_csv_robust(BASE_DIR / "products_raw.csv")
orders = read_csv_robust(BASE_DIR / "orders_raw.csv")

for column in customers.select_dtypes(include=["object", "string"]).columns:
    customers[column] = customers[column].map(
        lambda value: value.strip() if isinstance(value, str) else value
    )

customers["country_code"] = customers["country"].map(country_to_code)
customers = customers.drop_duplicates(subset=["customer_id"], keep="first")

products["price_eur"] = products["price_eur"].map(parse_number).astype(float)
products["in_stock"] = products["in_stock"].map(parse_boolean).astype("boolean")

orders["quantity"] = orders["quantity"].map(parse_number)
orders["unit_price_eur"] = orders["unit_price_eur"].map(parse_number)

customer_lookup = customers[["customer_id", "country_code"]].rename(
    columns={"country_code": "_customer_country_code"}
)
product_lookup = products[["product_id", "category"]].rename(
    columns={"category": "_product_category"}
)

joined = orders.merge(customer_lookup, on="customer_id", how="left")
joined = joined.merge(product_lookup, on="product_id", how="left")

joined["country_code"] = joined["_customer_country_code"].fillna("UNKNOWN")
joined["category"] = joined["_product_category"]
joined["_revenue"] = joined["quantity"] * joined["unit_price_eur"]

group_columns = ["country_code", "category"]

if "order_id" in joined.columns:
    result = (
        joined.groupby(group_columns, dropna=False, observed=True)
        .agg(
            total_revenue_eur=("_revenue", lambda values: values.sum(min_count=1)),
            order_count=("order_id", "nunique"),
        )
        .reset_index()
    )
else:
    result = (
        joined.groupby(group_columns, dropna=False, observed=True)
        .agg(
            total_revenue_eur=("_revenue", lambda values: values.sum(min_count=1)),
            order_count=("_revenue", "size"),
        )
        .reset_index()
    )

result["total_revenue_eur"] = result["total_revenue_eur"].round(2)
result = result.sort_values("total_revenue_eur", ascending=False, kind="mergesort").reset_index(drop=True)

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
result.to_parquet(OUTPUT_PATH, index=False)