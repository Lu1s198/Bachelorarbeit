import os
import pandas as pd
from dateutil import parser

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/customers_raw.csv"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/cleaning/google_v2_few_shot_r2/output.parquet"

df = pd.read_csv(input_path)

# Step 1: Trim text columns and replace missing values in 'country' with 'UNKNOWN'
for col in df.select_dtypes(include=["object"]).columns:
    df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

df["country"] = df["country"].fillna("UNKNOWN")
df.loc[df["country"].str.strip() == "", "country"] = "UNKNOWN"


# Step 2: Normalize 'registered_at' to YYYY-MM-DD ISO format
def parse_date(val):
    if pd.isna(val):
        return None
    val_str = str(val).strip()
    if not val_str or val_str.lower() == "nan":
        return None
    try:
        num = float(val_str)
        if num > 100000000:
            return pd.to_datetime(num, unit="s").strftime("%Y-%m-%d")
    except ValueError:
        pass

    try:
        dt = parser.parse(val_str, dayfirst=True)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None


df["registered_at"] = df["registered_at"].apply(parse_date)

# Step 3: Standardize 'country' to ISO-3166-1-alpha-2
COUNTRY_MAP = {
    "DE": "DE",
    "DEU": "DE",
    "GER": "DE",
    "GERMANY": "DE",
    "DEUTSCHLAND": "DE",
    "BUNDESREPUBLIK DEUTSCHLAND": "DE",
    "AT": "AT",
    "AUT": "AT",
    "AUSTRIA": "AT",
    "ÖSTERREICH": "AT",
    "OESTERREICH": "AT",
    "CH": "CH",
    "CHE": "CH",
    "SWITZERLAND": "CH",
    "SCHWEIZ": "CH",
    "SUI": "CH",
    "US": "US",
    "USA": "US",
    "UNITED STATES": "US",
    "UNITED STATES OF AMERICA": "US",
    "VEREINIGTE STAATEN": "US",
    "VEREINIGTE STAATEN VON AMERIKA": "US",
    "GB": "GB",
    "GBR": "GB",
    "UK": "GB",
    "UNITED KINGDOM": "GB",
    "GREAT BRITAIN": "GB",
    "GROSSBRITANNIEN": "GB",
    "VEREINIGTES KÖNIGREICH": "GB",
    "VEREINIGTES KOENIGREICH": "GB",
    "FR": "FR",
    "FRA": "FR",
    "FRANCE": "FR",
    "FRANKREICH": "FR",
    "IT": "IT",
    "ITA": "IT",
    "ITALY": "IT",
    "ITALIEN": "IT",
    "ES": "ES",
    "ESP": "ES",
    "SPAIN": "ES",
    "SPANIEN": "ES",
    "NL": "NL",
    "NLD": "NL",
    "NED": "NL",
    "NETHERLANDS": "NL",
    "THE NETHERLANDS": "NL",
    "NIEDERLANDE": "NL",
    "PL": "PL",
    "POL": "PL",
    "POLAND": "PL",
    "POLEN": "PL",
    "CA": "CA",
    "CAN": "CA",
    "CANADA": "CA",
    "KANADA": "CA",
    "CN": "CN",
    "CHN": "CN",
    "CHINA": "CN",
    "JP": "JP",
    "JPN": "JP",
    "JAPAN": "JP",
    "IN": "IN",
    "IND": "IN",
    "INDIA": "IN",
    "INDIEN": "IN",
    "BR": "BR",
    "BRA": "BR",
    "BRAZIL": "BR",
    "BRASILIEN": "BR",
    "AU": "AU",
    "AUS": "AU",
    "AUSTRALIA": "AU",
    "AUSTRALIEN": "AU",
    "RU": "RU",
    "RUS": "RU",
    "RUSSIA": "RU",
    "RUSSLAND": "RU",
    "SE": "SE",
    "SWE": "SE",
    "SWEDEN": "SE",
    "SCHWEDEN": "SE",
    "NO": "NO",
    "NOR": "NO",
    "NORWAY": "NO",
    "NORWEGEN": "NO",
    "DK": "DK",
    "DNK": "DK",
    "DENMARK": "DK",
    "DÄNEMARK": "DK",
    "DAENEMARK": "DK",
    "FI": "FI",
    "FIN": "FI",
    "FINLAND": "FI",
    "FINNLAND": "FI",
    "BE": "BE",
    "BEL": "BE",
    "BELGIUM": "BE",
    "BELGIEN": "BE",
    "LU": "LU",
    "LUX": "LU",
    "LUXEMBOURG": "LU",
    "LUXEMBURG": "LU",
    "PT": "PT",
    "PRT": "PT",
    "PORTUGAL": "PT",
    "POR": "PT",
    "GR": "GR",
    "GRC": "GR",
    "GREECE": "GR",
    "GRIECHENLAND": "GR",
    "IE": "IE",
    "IRL": "IE",
    "IRELAND": "IE",
    "IRLAND": "IE",
    "CZ": "CZ",
    "CZE": "CZ",
    "CZECH REPUBLIC": "CZ",
    "CZECHIA": "CZ",
    "TSCHECHIEN": "CZ",
    "TR": "TR",
    "TUR": "TR",
    "TURKEY": "TR",
    "TÜRKEI": "TR",
    "TUERKEI": "TR",
    "UNKNOWN": "UNKNOWN",
}


def map_country(val):
    if pd.isna(val):
        return "UNKNOWN"
    val_clean = str(val).strip().upper()
    if not val_clean or val_clean == "UNKNOWN":
        return "UNKNOWN"
    if val_clean in COUNTRY_MAP:
        return COUNTRY_MAP[val_clean]
    try:
        import pycountry

        c = (
            pycountry.countries.get(alpha_2=val_clean)
            or pycountry.countries.get(alpha_3=val_clean)
            or pycountry.countries.get(name=val_clean)
        )
        if c:
            return c.alpha_2
        results = pycountry.countries.search_fuzzy(val_clean)
        if results:
            return results[0].alpha_2
    except Exception:
        pass
    return "UNKNOWN"


df["country"] = df["country"].apply(map_country)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)