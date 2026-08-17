# ETL Task: Customer Data Cleaning
# Sub-steps:
# 1. Trim whitespace from all text columns; fill missing 'country' values with 'UNKNOWN'
# 2. Normalize 'registered_at' to ISO format YYYY-MM-DD from mixed formats:
#    - ISO date (YYYY-MM-DD)
#    - German format (TT.MM.JJJJ)
#    - US format ('Month DD YYYY')
#    - Unix timestamp (seconds)
# 3. Normalize 'country' to ISO-3166-1 alpha-2 codes, mapping various German/English
#    names/abbreviations; unmappable values become 'UNKNOWN'

import pandas as pd
import numpy as np
import re

# ---------- Load Input ----------
input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/customers_raw.csv"
df = pd.read_csv(input_path, dtype={"customer_id": "int64"})

# ============================================================
# STEP 1: Trim whitespace in text columns, fill missing country
# ============================================================

# Identify text/object columns (works across different pandas versions,
# using select_dtypes instead of relying on a specific string dtype idiom)
text_cols = df.select_dtypes(include=["object"]).columns.tolist()

for col in text_cols:
    # Use .str.strip() but guard against non-string entries (e.g. NaN)
    df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

# Fill missing values in 'country' with 'UNKNOWN'
# Handles NaN, None, and also empty strings that might result from stripping
df["country"] = df["country"].replace("", np.nan)
df["country"] = df["country"].fillna("UNKNOWN")

# ============================================================
# STEP 2: Normalize 'registered_at' to ISO format YYYY-MM-DD
# ============================================================

def normalize_date(value):
    """
    Try to parse a date value from multiple possible formats:
    - ISO format (YYYY-MM-DD)
    - German format (DD.MM.YYYY)
    - US format ('Month DD YYYY')
    - Unix timestamp (seconds, as int/float or numeric string)
    Returns ISO string 'YYYY-MM-DD' or NaN if parsing fails.
    """
    if pd.isna(value):
        return np.nan

    s = str(value).strip()
    if s == "":
        return np.nan

    # Try Unix timestamp (numeric string or number)
    # Heuristic: if the string is purely numeric and has a length typical
    # for a timestamp in seconds (commonly 9-10 digits), treat as such.
    if re.fullmatch(r"\d+(\.\d+)?", s):
        try:
            ts = float(s)
            # Reasonable range check for seconds-based timestamps
            # (e.g. between year 1970 and ~2100)
            if 0 < ts < 4102444800:  # 2100-01-01 in seconds
                dt = pd.to_datetime(ts, unit="s", errors="coerce")
                if pd.notna(dt):
                    return dt.strftime("%Y-%m-%d")
        except (ValueError, OverflowError):
            pass

    # Try German format DD.MM.YYYY
    try:
        dt = pd.to_datetime(s, format="%d.%m.%Y", errors="raise")
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        pass

    # Try US format 'Month DD YYYY' (e.g. 'January 05 2020')
    try:
        dt = pd.to_datetime(s, format="%B %d %Y", errors="raise")
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        pass

    # Try ISO format YYYY-MM-DD directly
    try:
        dt = pd.to_datetime(s, format="%Y-%m-%d", errors="raise")
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        pass

    # Fallback: let pandas try to infer the format generically
    try:
        dt = pd.to_datetime(s, errors="raise", dayfirst=False)
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return np.nan

df["registered_at"] = df["registered_at"].apply(normalize_date)

# ============================================================
# STEP 3: Normalize 'country' to ISO-3166-1 alpha-2 codes
# ============================================================

# Mapping table covering German/English names and common abbreviations
# Keys are normalized (uppercase, stripped) for robust matching
country_mapping = {
    # Germany
    "DE": "DE", "GERMANY": "DE", "DEUTSCHLAND": "DE", "GER": "DE", "D": "DE",
    # Austria
    "AT": "AT", "AUSTRIA": "AT", "OESTERREICH": "AT", "ÖSTERREICH": "AT", "AUT": "AT",
    # Switzerland
    "CH": "CH", "SWITZERLAND": "CH", "SCHWEIZ": "CH", "SUISSE": "CH", "CHE": "CH",
    # United States
    "US": "US", "USA": "US", "UNITED STATES": "US", "UNITED STATES OF AMERICA": "US",
    "VEREINIGTE STAATEN": "US", "AMERICA": "US",
    # United Kingdom
    "UK": "GB", "GB": "GB", "UNITED KINGDOM": "GB", "GREAT BRITAIN": "GB",
    "GROSSBRITANNIEN": "GB", "GROßBRITANNIEN": "GB", "ENGLAND": "GB",
    # France
    "FR": "FR", "FRANCE": "FR", "FRANKREICH": "FR", "FRA": "FR",
    # Italy
    "IT": "IT", "ITALY": "IT", "ITALIEN": "IT", "ITA": "IT",
    # Spain
    "ES": "ES", "SPAIN": "ES", "SPANIEN": "ES", "ESP": "ES",
    # Netherlands
    "NL": "NL", "NETHERLANDS": "NL", "NIEDERLANDE": "NL", "HOLLAND": "NL", "NLD": "NL",
    # Belgium
    "BE": "BE", "BELGIUM": "BE", "BELGIEN": "BE", "BEL": "BE",
    # Poland
    "PL": "PL", "POLAND": "PL", "POLEN": "PL", "POL": "PL",
    # Portugal
    "PT": "PT", "PORTUGAL": "PT", "PRT": "PT",
    # Sweden
    "SE": "SE", "SWEDEN": "SE", "SCHWEDEN": "SE", "SWE": "SE",
    # Norway
    "NO": "NO", "NORWAY": "NO", "NORWEGEN": "NO", "NOR": "NO",
    # Denmark
    "DK": "DK", "DENMARK": "DK", "DAENEMARK": "DK", "DÄNEMARK": "DK", "DNK": "DK",
    # Finland
    "FI": "FI", "FINLAND": "FI", "FINNLAND": "FI", "FIN": "FI",
    # Ireland
    "IE": "IE", "IRELAND": "IE", "IRLAND": "IE", "IRL": "IE",
    # Luxembourg
    "LU": "LU", "LUXEMBOURG": "LU", "LUXEMBURG": "LU", "LUX": "LU",
    # Czech Republic
    "CZ": "CZ", "CZECH REPUBLIC": "CZ", "TSCHECHIEN": "CZ", "CZE": "CZ",
    # Hungary
    "HU": "HU", "HUNGARY": "HU", "UNGARN": "HU", "HUN": "HU",
    # Greece
    "GR": "GR", "GREECE": "GR", "GRIECHENLAND": "GR", "GRC": "GR",
    # Canada
    "CA": "CA", "CANADA": "CA", "KANADA": "CA", "CAN": "CA",
    # Australia
    "AU": "AU", "AUSTRALIA": "AU", "AUSTRALIEN": "AU", "AUS": "AU",
    # China
    "CN": "CN", "CHINA": "CN", "CHN": "CN",
    # Japan
    "JP": "JP", "JAPAN": "JP", "JPN": "JP",
    # India
    "IN": "IN", "INDIA": "IN", "INDIEN": "IN", "IND": "IN",
    # Brazil
    "BR": "BR", "BRAZIL": "BR", "BRASILIEN": "BR", "BRA": "BR",
    # Russia
    "RU": "RU", "RUSSIA": "RU", "RUSSLAND": "RU", "RUS": "RU",
    # Turkey
    "TR": "TR", "TURKEY": "TR", "TUERKEI": "TR", "TÜRKEI": "TR", "TUR": "TR",
}

def normalize_country(value):
    """
    Map country value to ISO-3166-1 alpha-2 code using the mapping table.
    Returns 'UNKNOWN' if the value cannot be uniquely mapped.
    """
    if pd.isna(value):
        return "UNKNOWN"

    s = str(value).strip().upper()
    if s == "" or s == "UNKNOWN":
        return "UNKNOWN"

    # Direct lookup in mapping table (covers codes, abbreviations, names)
    if s in country_mapping:
        return country_mapping[s]

    return "UNKNOWN"

df["country"] = df["country"].apply(normalize_country)

# ============================================================
# Write output as Parquet
# ============================================================
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/cleaning/anthropic_v3_chain_of_thought_r2/output.parquet"
df.to_parquet(output_path, index=False)