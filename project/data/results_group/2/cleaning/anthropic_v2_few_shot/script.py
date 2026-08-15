import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta

df = pd.read_csv("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/customers_raw.csv")

# --- Step 1: trim whitespace in text columns, fill missing country ---
text_columns = df.select_dtypes(include="object").columns
for column in text_columns:
    df[column] = df[column].astype(str).str.strip()
    df[column] = df[column].replace({"nan": np.nan, "None": np.nan, "": np.nan})

df["country"] = df["country"].fillna("UNKNOWN")
df["country"] = df["country"].replace("", "UNKNOWN")

# --- Step 2: normalize registered_at to ISO format YYYY-MM-DD ---
def parse_date(value):
    if pd.isna(value):
        return np.nan
    val = str(value).strip()
    if val == "" or val.lower() == "nan":
        return np.nan

    # Unix timestamp (all digits)
    if re.fullmatch(r"\d{9,10}", val):
        try:
            dt = datetime(1970, 1, 1) + timedelta(seconds=int(val))
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    # ISO format YYYY-MM-DD
    try:
        dt = datetime.strptime(val, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        pass

    # German format DD.MM.YYYY
    try:
        dt = datetime.strptime(val, "%d.%m.%Y")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        pass

    # US format 'Month DD YYYY'
    try:
        dt = datetime.strptime(val, "%B %d %Y")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        pass

    # Fallback: try pandas generic parser
    try:
        dt = pd.to_datetime(val, errors="coerce")
        if pd.notna(dt):
            return dt.strftime("%Y-%m-%d")
    except Exception:
        pass

    return np.nan

df["registered_at"] = df["registered_at"].apply(parse_date)

# --- Step 3: normalize country to ISO-3166-1 alpha-2 code ---
country_map = {
    # Germany
    "germany": "DE", "deutschland": "DE", "de": "DE", "ger": "DE", "deu": "DE",
    # USA
    "united states": "US", "united states of america": "US", "usa": "US",
    "us": "US", "vereinigte staaten": "US", "vereinigte staaten von amerika": "US",
    # United Kingdom
    "united kingdom": "GB", "uk": "GB", "great britain": "GB", "gb": "GB",
    "grossbritannien": "GB", "großbritannien": "GB", "vereinigtes königreich": "GB",
    "vereinigtes koenigreich": "GB",
    # France
    "france": "FR", "frankreich": "FR", "fr": "FR",
    # Spain
    "spain": "ES", "spanien": "ES", "es": "ES",
    # Italy
    "italy": "IT", "italien": "IT", "it": "IT",
    # Netherlands
    "netherlands": "NL", "niederlande": "NL", "nl": "NL", "holland": "NL",
    # Belgium
    "belgium": "BE", "belgien": "BE", "be": "BE",
    # Switzerland
    "switzerland": "CH", "schweiz": "CH", "ch": "CH",
    # Austria
    "austria": "AT", "österreich": "AT", "oesterreich": "AT", "at": "AT",
    # Poland
    "poland": "PL", "polen": "PL", "pl": "PL",
    # Portugal
    "portugal": "PT", "pt": "PT",
    # Sweden
    "sweden": "SE", "schweden": "SE", "se": "SE",
    # Norway
    "norway": "NO", "norwegen": "NO", "no": "NO",
    # Denmark
    "denmark": "DK", "dänemark": "DK", "daenemark": "DK", "dk": "DK",
    # Finland
    "finland": "FI", "finnland": "FI", "fi": "FI",
    # Ireland
    "ireland": "IE", "irland": "IE", "ie": "IE",
    # Greece
    "greece": "GR", "griechenland": "GR", "gr": "GR",
    # Czech Republic
    "czech republic": "CZ", "tschechien": "CZ", "cz": "CZ",
    # Hungary
    "hungary": "HU", "ungarn": "HU", "hu": "HU",
    # Canada
    "canada": "CA", "kanada": "CA", "ca": "CA",
    # Australia
    "australia": "AU", "australien": "AU", "au": "AU",
    # China
    "china": "CN", "cn": "CN",
    # Japan
    "japan": "JP", "jp": "JP",
    # India
    "india": "IN", "indien": "IN", "in": "IN",
    # Brazil
    "brazil": "BR", "brasilien": "BR", "br": "BR",
    # Russia
    "russia": "RU", "russland": "RU", "ru": "RU",
    # Mexico
    "mexico": "MX", "mexiko": "MX", "mx": "MX",
    # South Africa
    "south africa": "ZA", "südafrika": "ZA", "suedafrika": "ZA", "za": "ZA",
}

valid_alpha2 = set(country_map.values())

def normalize_country(value):
    if pd.isna(value):
        return "UNKNOWN"
    val = str(value).strip()
    if val == "" or val.upper() == "UNKNOWN":
        return "UNKNOWN"

    if len(val) == 2 and val.upper() in valid_alpha2:
        return val.upper()

    key = val.lower()
    if key in country_map:
        return country_map[key]

    return "UNKNOWN"

df["country"] = df["country"].apply(normalize_country)

df.to_parquet(
    "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/cleaning/anthropic_v2_few_shot/output.parquet",
    index=False,
)