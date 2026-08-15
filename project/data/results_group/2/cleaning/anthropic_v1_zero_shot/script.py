import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/customers_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/cleaning/anthropic_v1_zero_shot/output.parquet"

df = pd.read_csv(input_path, dtype={"customer_id": "int64"})

# Step 1: Strip whitespace from text columns, fill missing country with 'UNKNOWN'
text_cols = df.select_dtypes(include=["object"]).columns
for col in text_cols:
    df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

if "country" in df.columns:
    df["country"] = df["country"].replace(r'^\s*$', np.nan, regex=True)
    df["country"] = df["country"].where(pd.notna(df["country"]), "UNKNOWN")
    df["country"] = df["country"].fillna("UNKNOWN")

# Step 2: Normalize registered_at to ISO format YYYY-MM-DD
def normalize_date(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s == "" or s.lower() == "nan":
        return None

    # Try Unix timestamp (all digits, reasonable length)
    if re.fullmatch(r'\d+(\.\d+)?', s):
        try:
            ts = float(s)
            if ts > 1e6:  # plausible unix timestamp in seconds
                dt = datetime(1970, 1, 1) + timedelta(seconds=ts)
                return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    # Try ISO format YYYY-MM-DD
    m = re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})', s)
    if m:
        try:
            dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    # Try German format DD.MM.YYYY
    m = re.fullmatch(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', s)
    if m:
        try:
            dt = datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    # Try US format 'Month DD YYYY'
    try:
        dt = datetime.strptime(s, "%B %d %Y")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        pass

    try:
        dt = datetime.strptime(s, "%b %d %Y")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        pass

    # Fallback: try pandas parser
    try:
        dt = pd.to_datetime(s, errors="coerce")
        if pd.notna(dt):
            return dt.strftime("%Y-%m-%d")
    except Exception:
        pass

    return None

df["registered_at"] = df["registered_at"].apply(normalize_date)

# Step 3: Normalize country to ISO 3166-1 alpha-2 code
country_map = {
    # Germany
    "germany": "DE", "deutschland": "DE", "de": "DE", "ger": "DE", "deu": "DE",
    "d": "DE", "germ": "DE",
    # Austria
    "austria": "AT", "österreich": "AT", "oesterreich": "AT", "at": "AT", "aut": "AT",
    # Switzerland
    "switzerland": "CH", "schweiz": "CH", "ch": "CH", "che": "CH", "suisse": "CH",
    # United States
    "united states": "US", "united states of america": "US", "usa": "US", "us": "US",
    "vereinigte staaten": "US", "america": "US", "u.s.a.": "US", "u.s.": "US",
    # United Kingdom
    "united kingdom": "GB", "uk": "GB", "gb": "GB", "great britain": "GB",
    "großbritannien": "GB", "grossbritannien": "GB", "england": "GB",
    "vereinigtes königreich": "GB", "vereinigtes koenigreich": "GB",
    # France
    "france": "FR", "frankreich": "FR", "fr": "FR", "fra": "FR",
    # Italy
    "italy": "IT", "italien": "IT", "it": "IT", "ita": "IT",
    # Spain
    "spain": "ES", "spanien": "ES", "es": "ES", "esp": "ES",
    # Netherlands
    "netherlands": "NL", "niederlande": "NL", "nl": "NL", "nld": "NL", "holland": "NL",
    # Belgium
    "belgium": "BE", "belgien": "BE", "be": "BE", "bel": "BE",
    # Poland
    "poland": "PL", "polen": "PL", "pl": "PL", "pol": "PL",
    # Portugal
    "portugal": "PT", "pt": "PT", "prt": "PT",
    # Sweden
    "sweden": "SE", "schweden": "SE", "se": "SE", "swe": "SE",
    # Norway
    "norway": "NO", "norwegen": "NO", "no": "NO", "nor": "NO",
    # Denmark
    "denmark": "DK", "dänemark": "DK", "daenemark": "DK", "dk": "DK", "dnk": "DK",
    # Finland
    "finland": "FI", "finnland": "FI", "fi": "FI", "fin": "FI",
    # Ireland
    "ireland": "IE", "irland": "IE", "ie": "IE", "irl": "IE",
    # Canada
    "canada": "CA", "kanada": "CA", "ca": "CA", "can": "CA",
    # Australia
    "australia": "AU", "australien": "AU", "au": "AU", "aus": "AU",
    # China
    "china": "CN", "cn": "CN", "chn": "CN",
    # Japan
    "japan": "JP", "jp": "JP", "jpn": "JP",
    # India
    "india": "IN", "indien": "IN", "in": "IN", "ind": "IN",
    # Brazil
    "brazil": "BR", "brasilien": "BR", "br": "BR", "bra": "BR",
    # Mexico
    "mexico": "MX", "mexiko": "MX", "mx": "MX", "mex": "MX",
    # Russia
    "russia": "RU", "russland": "RU", "ru": "RU", "rus": "RU",
    # Czech Republic
    "czech republic": "CZ", "tschechien": "CZ", "cz": "CZ", "cze": "CZ",
    # Greece
    "greece": "GR", "griechenland": "GR", "gr": "GR", "grc": "GR",
    # Hungary
    "hungary": "HU", "ungarn": "HU", "hu": "HU", "hun": "HU",
    # Turkey
    "turkey": "TR", "türkei": "TR", "tuerkei": "TR", "tr": "TR", "tur": "TR",
    # South Korea
    "south korea": "KR", "südkorea": "KR", "suedkorea": "KR", "kr": "KR", "kor": "KR",
    # New Zealand
    "new zealand": "NZ", "neuseeland": "NZ", "nz": "NZ", "nzl": "NZ",
    # South Africa
    "south africa": "ZA", "südafrika": "ZA", "suedafrika": "ZA", "za": "ZA", "zaf": "ZA",
    # Unknown
    "unknown": "UNKNOWN", "unbekannt": "UNKNOWN", "": "UNKNOWN",
}

def normalize_country(val):
    if pd.isna(val):
        return "UNKNOWN"
    s = str(val).strip()
    if s == "" or s.lower() == "nan":
        return "UNKNOWN"
    s_lower = s.lower()
    if s_lower in country_map:
        return country_map[s_lower]
    # Check if already a valid 2-letter code (uppercase check)
    if re.fullmatch(r'[A-Za-z]{2}', s):
        code = s.upper()
        # verify it's in our known set of codes
        known_codes = set(country_map.values())
        known_codes.discard("UNKNOWN")
        if code in known_codes:
            return code
    return "UNKNOWN"

df["country"] = df["country"].apply(normalize_country)

df.to_parquet(output_path, index=False)