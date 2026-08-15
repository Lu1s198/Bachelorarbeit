import os
import re
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/customers_raw.csv"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/cleaning/google_v2_few_shot/output.parquet"

df = pd.read_csv(input_path)

# Step 1: Strip whitespace in text columns and handle missing country values
text_cols = ["full_name", "email", "country", "registered_at"]
for col in text_cols:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()

df["country"] = df["country"].replace(["nan", "None", "NaN", ""], pd.NA).fillna("UNKNOWN")
df["country"] = df["country"].replace("UNKNOWN", "UNKNOWN")

# Step 2: Normalize registered_at to YYYY-MM-DD
def parse_date(val):
    if pd.isna(val) or val in ["nan", "None", "", "UNKNOWN"]:
        return None
    val_str = str(val).strip()
    if re.match(r"^\d+(\.\d+)?$", val_str):
        num = float(val_str)
        if 0 <= num <= 4102444800:
            try:
                return pd.to_datetime(num, unit="s").strftime("%Y-%m-%d")
            except Exception:
                pass
    if "." in val_str:
        dt = pd.to_datetime(val_str, format="%d.%m.%Y", errors="coerce")
        if pd.notna(dt):
            return dt.strftime("%Y-%m-%d")
    dt = pd.to_datetime(val_str, errors="coerce")
    if pd.notna(dt):
        return dt.strftime("%Y-%m-%d")
    return val_str

df["registered_at"] = df["registered_at"].apply(parse_date)

# Step 3: Standardize country to ISO 3166-1 alpha-2
COUNTRY_MAP = {
    "DE": "DE", "DEU": "DE", "GERMANY": "DE", "DEUTSCHLAND": "DE", "GER": "DE",
    "AT": "AT", "AUT": "AT", "AUSTRIA": "AT", "ÖSTERREICH": "AT", "OESTERREICH": "AT",
    "CH": "CH", "CHE": "CH", "SWITZERLAND": "CH", "SCHWEIZ": "CH",
    "US": "US", "USA": "US", "UNITED STATES": "US", "UNITED STATES OF AMERICA": "US", "VEREINIGTE STAATEN": "US",
    "GB": "GB", "GBR": "GB", "UK": "GB", "UNITED KINGDOM": "GB", "GROSSBRITANNIEN": "GB", "GROßBRITANNIEN": "GB",
    "FR": "FR", "FRA": "FR", "FRANCE": "FR", "FRANKREICH": "FR",
    "IT": "IT", "ITA": "IT", "ITALY": "IT", "ITALIEN": "IT",
    "ES": "ES", "ESP": "ES", "SPAIN": "ES", "SPANIEN": "ES",
    "NL": "NL", "NLD": "NL", "NETHERLANDS": "NL", "NIEDERLANDE": "NL", "HOLLAND": "NL",
    "CA": "CA", "CAN": "CA", "CANADA": "CA", "KANADA": "CA",
    "PL": "PL", "POL": "PL", "POLAND": "PL", "POLEN": "PL",
    "CZ": "CZ", "CZE": "CZ", "CZECH REPUBLIC": "CZ", "CZECHIA": "CZ", "TSCHECHIEN": "CZ",
    "BE": "BE", "BEL": "BE", "BELGIUM": "BE", "BELGIEN": "BE",
    "SE": "SE", "SWE": "SE", "SWEDEN": "SE", "SCHWEDEN": "SE",
    "DK": "DK", "DNK": "DK", "DENMARK": "DK", "DÄNEMARK": "DK", "DAENEMARK": "DK",
    "NO": "NO", "NOR": "NO", "NORWAY": "NO", "NORWEGEN": "NO",
    "FI": "FI", "FIN": "FI", "FINLAND": "FI", "FINNLAND": "FI",
    "PT": "PT", "PRT": "PT", "PORTUGAL": "PT",
    "BR": "BR", "BRA": "BR", "BRAZIL": "BR", "BRASILIEN": "BR",
    "CN": "CN", "CHN": "CN", "CHINA": "CN",
    "JP": "JP", "JPN": "JP", "JAPAN": "JP",
    "IN": "IN", "IND": "IN", "INDIA": "IN", "INDIEN": "IN",
    "AU": "AU", "AUS": "AU", "AUSTRALIA": "AU", "AUSTRALIEN": "AU",
    "RU": "RU", "RUS": "RU", "RUSSIA": "RU", "RUSSLAND": "RU",
    "TR": "TR", "TUR": "TR", "TURKEY": "TR", "TÜRKEI": "TR", "TUERKEI": "TR"
}

def normalize_country(val):
    if pd.isna(val):
        return "UNKNOWN"
    s = str(val).strip().upper()
    if not s or s in ["UNKNOWN", "NAN", "NONE"]:
        return "UNKNOWN"
    if s in COUNTRY_MAP:
        return COUNTRY_MAP[s]
    try:
        import pycountry
        c = pycountry.countries.get(alpha_2=s) or pycountry.countries.get(alpha_3=s) or pycountry.countries.get(name=s)
        if c:
            return c.alpha_2
        res = pycountry.countries.search_fuzzy(s)
        if res:
            return res[0].alpha_2
    except Exception:
        pass
    return "UNKNOWN"

df["country"] = df["country"].apply(normalize_country)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)