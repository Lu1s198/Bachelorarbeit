import pandas as pd
import numpy as np
import re

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/customers_raw.csv"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/cleaning/anthropic_v2_few_shot_r2/output.parquet"

df = pd.read_csv(input_path)

# Step 1: trim whitespace in text columns, fillna country with UNKNOWN
text_cols = df.select_dtypes(include="object").columns
for column in text_cols:
    df[column] = df[column].str.strip()

df["country"] = df["country"].replace("", np.nan)
df["country"] = df["country"].fillna("UNKNOWN")

# Step 2: normalize registered_at to ISO format YYYY-MM-DD
def parse_date(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s == "":
        return None

    # Unix timestamp (seconds) - all digits, possibly long number
    if re.fullmatch(r"\d{9,10}", s):
        try:
            dt = pd.to_datetime(int(s), unit="s")
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    # ISO format YYYY-MM-DD
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        try:
            dt = pd.to_datetime(s, format="%Y-%m-%d")
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    # German format DD.MM.YYYY
    if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", s):
        try:
            dt = pd.to_datetime(s, format="%d.%m.%Y")
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    # US format "Month DD YYYY"
    try:
        dt = pd.to_datetime(s, format="%B %d %Y")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        pass

    # Fallback generic parse
    try:
        dt = pd.to_datetime(s)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None

df["registered_at"] = df["registered_at"].apply(parse_date)

# Step 3: normalize country to ISO alpha-2 codes
country_map = {
    "germany": "DE", "deutschland": "DE", "de": "DE", "ger": "DE", "deu": "DE",
    "usa": "US", "united states": "US", "united states of america": "US", "us": "US",
    "vereinigte staaten": "US", "america": "US", "usa.": "US",
    "uk": "GB", "united kingdom": "GB", "great britain": "GB", "gb": "GB",
    "grossbritannien": "GB", "großbritannien": "GB", "england": "GB",
    "france": "FR", "frankreich": "FR", "fr": "FR",
    "spain": "ES", "spanien": "ES", "es": "ES",
    "italy": "IT", "italien": "IT", "it": "IT",
    "netherlands": "NL", "niederlande": "NL", "nl": "NL", "holland": "NL",
    "austria": "AT", "österreich": "AT", "oesterreich": "AT", "at": "AT",
    "switzerland": "CH", "schweiz": "CH", "ch": "CH",
    "belgium": "BE", "belgien": "BE", "be": "BE",
    "poland": "PL", "polen": "PL", "pl": "PL",
    "portugal": "PT", "pt": "PT",
    "sweden": "SE", "schweden": "SE", "se": "SE",
    "norway": "NO", "norwegen": "NO", "no": "NO",
    "denmark": "DK", "dänemark": "DK", "daenemark": "DK", "dk": "DK",
    "finland": "FI", "finnland": "FI", "fi": "FI",
    "ireland": "IE", "irland": "IE", "ie": "IE",
    "greece": "GR", "griechenland": "GR", "gr": "GR",
    "czech republic": "CZ", "tschechien": "CZ", "cz": "CZ",
    "canada": "CA", "kanada": "CA", "ca": "CA",
    "australia": "AU", "australien": "AU", "au": "AU",
    "china": "CN", "cn": "CN",
    "japan": "JP", "jp": "JP",
    "india": "IN", "indien": "IN", "in": "IN",
    "brazil": "BR", "brasilien": "BR", "br": "BR",
    "russia": "RU", "russland": "RU", "ru": "RU",
    "mexico": "MX", "mexiko": "MX", "mx": "MX",
    "hungary": "HU", "ungarn": "HU", "hu": "HU",
    "romania": "RO", "rumänien": "RO", "rumaenien": "RO", "ro": "RO",
    "turkey": "TR", "türkei": "TR", "tuerkei": "TR", "tr": "TR",
    "unknown": "UNKNOWN",
}

valid_iso_codes = set(v for v in country_map.values() if v != "UNKNOWN")

def normalize_country(val):
    if pd.isna(val):
        return "UNKNOWN"
    s = str(val).strip().lower()
    if s == "" or s == "unknown":
        return "UNKNOWN"
    if s in country_map:
        return country_map[s]
    # already a valid 2-letter code (case-insensitive) that's in our known set
    upper = str(val).strip().upper()
    if len(upper) == 2 and upper in valid_iso_codes:
        return upper
    return "UNKNOWN"

df["country"] = df["country"].apply(normalize_country)

df.to_parquet(output_path, index=False)