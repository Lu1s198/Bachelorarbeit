# -*- coding: utf-8 -*-
# ETL Task: Clean and normalize customer data
#
# Sub-steps:
# Step 1: Trim whitespace from all text columns, fill missing country with 'UNKNOWN'
#   - Handle different pandas/numpy versions for NA detection (isna/isnull work across versions)
#   - Apply str.strip() only to string/object columns
#
# Step 2: Normalize registered_at to ISO format YYYY-MM-DD
#   - Handle multiple formats: ISO (YYYY-MM-DD), German (DD.MM.YYYY), 
#     US (Month DD YYYY), Unix timestamp (seconds since epoch)
#   - Try each parsing strategy in sequence, use first successful one
#
# Step 3: Unify country column to ISO-3166-1 alpha-2 codes
#   - Build a mapping dictionary covering German/English names and abbreviations
#   - Case-insensitive matching, normalize to uppercase codes
#   - Unmatched values -> 'UNKNOWN'

import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta

# -----------------------------
# Load input data
# -----------------------------
input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/customers_raw.csv"
df = pd.read_csv(input_path, dtype={
    "customer_id": "int64",
    "full_name": "str",
    "email": "str",
    "country": "str",
    "registered_at": "str"
})

# =====================================================
# STEP 1: Trim whitespace, fill missing country
# =====================================================

# Identify text/object columns (works across pandas versions)
text_cols = df.select_dtypes(include=["object"]).columns.tolist()

for col in text_cols:
    # Use .where + str.strip; handle NA-safe stripping across pandas versions
    # astype(str) would convert NaN to 'nan', so we mask NA first
    mask_notna = df[col].notna()
    df.loc[mask_notna, col] = df.loc[mask_notna, col].astype(str).str.strip()

# Fill missing values in 'country' with 'UNKNOWN'
# Also treat empty strings (after stripping) as missing
df["country"] = df["country"].replace(r"^\s*$", np.nan, regex=True)
df["country"] = df["country"].fillna("UNKNOWN")

# =====================================================
# STEP 2: Normalize registered_at to ISO format YYYY-MM-DD
# =====================================================

def parse_date(value):
    """
    Try multiple date formats in sequence:
    1. ISO format (YYYY-MM-DD)
    2. German format (DD.MM.YYYY)
    3. US format (Month DD YYYY, e.g. 'January 05 2020')
    4. Unix timestamp (seconds since epoch, numeric string)
    Returns ISO date string or None if unparseable.
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None

    v = str(value).strip()
    if v == "" or v.lower() == "nan":
        return None

    # Try Unix timestamp (numeric, seconds since epoch)
    if re.fullmatch(r"\d{9,10}(\.\d+)?", v):
        try:
            ts = float(v)
            dt = datetime(1970, 1, 1) + timedelta(seconds=ts)
            return dt.strftime("%Y-%m-%d")
        except (ValueError, OverflowError):
            pass

    # Try ISO format YYYY-MM-DD
    try:
        dt = datetime.strptime(v, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass

    # Try German format DD.MM.YYYY
    try:
        dt = datetime.strptime(v, "%d.%m.%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass

    # Try US format 'Month DD YYYY' (e.g. 'January 05 2020')
    try:
        dt = datetime.strptime(v, "%B %d %Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass

    # If nothing matches, try pandas' flexible parser as fallback
    try:
        dt = pd.to_datetime(v, errors="raise")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None

df["registered_at"] = df["registered_at"].apply(parse_date)

# =====================================================
# STEP 3: Unify country column to ISO-3166-1 alpha-2 codes
# =====================================================

# Comprehensive mapping: German/English names & common abbreviations -> ISO alpha-2
country_map = {
    # Germany
    "germany": "DE", "deutschland": "DE", "de": "DE", "ger": "DE", "deu": "DE",
    # USA
    "united states": "US", "united states of america": "US", "usa": "US",
    "us": "US", "vereinigte staaten": "US", "vereinigte staaten von amerika": "US",
    # UK
    "united kingdom": "GB", "uk": "GB", "great britain": "GB",
    "großbritannien": "GB", "grossbritannien": "GB", "gb": "GB", "england": "GB",
    # France
    "france": "FR", "frankreich": "FR", "fr": "FR", "fra": "FR",
    # Spain
    "spain": "ES", "spanien": "ES", "es": "ES", "esp": "ES",
    # Italy
    "italy": "IT", "italien": "IT", "it": "IT", "ita": "IT",
    # Austria
    "austria": "AT", "österreich": "AT", "oesterreich": "AT", "at": "AT", "aut": "AT",
    # Switzerland
    "switzerland": "CH", "schweiz": "CH", "ch": "CH", "che": "CH",
    # Netherlands
    "netherlands": "NL", "niederlande": "NL", "nl": "NL", "nld": "NL",
    "the netherlands": "NL",
    # Belgium
    "belgium": "BE", "belgien": "BE", "be": "BE", "bel": "BE",
    # Poland
    "poland": "PL", "polen": "PL", "pl": "PL", "pol": "PL",
    # Portugal
    "portugal": "PT", "pt": "PT", "prt": "PT",
    # Sweden
    "sweden": "SE", "schweden": "SE", "se": "SE", "swe": "SE",
    # Denmark
    "denmark": "DK", "dänemark": "DK", "daenemark": "DK", "dk": "DK", "dnk": "DK",
    # Norway
    "norway": "NO", "norwegen": "NO", "no": "NO", "nor": "NO",
    # Finland
    "finland": "FI", "finnland": "FI", "fi": "FI", "fin": "FI",
    # Ireland
    "ireland": "IE", "irland": "IE", "ie": "IE", "irl": "IE",
    # Luxembourg
    "luxembourg": "LU", "luxemburg": "LU", "lu": "LU", "lux": "LU",
    # Greece
    "greece": "GR", "griechenland": "GR", "gr": "GR", "grc": "GR",
    # Czech Republic
    "czech republic": "CZ", "tschechien": "CZ", "cz": "CZ", "cze": "CZ",
    # Hungary
    "hungary": "HU", "ungarn": "HU", "hu": "HU", "hun": "HU",
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
    # Russia
    "russia": "RU", "russland": "RU", "ru": "RU", "rus": "RU",
    # Mexico
    "mexico": "MX", "mexiko": "MX", "mx": "MX", "mex": "MX",
    # UNKNOWN passthrough
    "unknown": "UNKNOWN",
}

def normalize_country(value):
    """
    Normalize country value to ISO-3166-1 alpha-2 code.
    Case-insensitive lookup in country_map; unmatched -> 'UNKNOWN'.
    """
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "UNKNOWN"
    v = str(value).strip().lower()
    if v == "" or v == "nan":
        return "UNKNOWN"
    return country_map.get(v, "UNKNOWN")

df["country"] = df["country"].apply(normalize_country)

# =====================================================
# Write result to Parquet
# =====================================================
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/cleaning/anthropic_v3_chain_of_thought/output.parquet"
df.to_parquet(output_path, index=False)