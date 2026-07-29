import os
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/cleaning_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/cleaning_hard/output.parquet"

df = pd.read_parquet(input_path)

iso2_map = {
    "DE": "DE", "DEU": "DE", "GER": "DE", "GERMANY": "DE", "DEUTSCHLAND": "DE",
    "US": "US", "USA": "US", "UNITED STATES": "US", "UNITED STATES OF AMERICA": "US", "U.S.": "US", "U.S.A.": "US",
    "GB": "GB", "GBR": "GB", "UK": "GB", "UNITED KINGDOM": "GB", "GREAT BRITAIN": "GB", "GROSSBRITANNIEN": "GB", "VEREINIGTES KÖNIGREICH": "GB", "VEREINIGTES KOENIGREICH": "GB",
    "FR": "FR", "FRA": "FR", "FRANCE": "FR", "FRANKREICH": "FR",
    "AT": "AT", "AUT": "AT", "AUSTRIA": "AT", "ÖSTERREICH": "AT", "OESTERREICH": "AT",
    "CH": "CH", "CHE": "CH", "SWITZERLAND": "CH", "SCHWEIZ": "CH", "SUISSE": "CH",
    "ES": "ES", "ESP": "ES", "SPAIN": "ES", "SPANIEN": "ES",
    "IT": "IT", "ITA": "IT", "ITALY": "IT", "ITALIEN": "IT",
    "NL": "NL", "NLD": "NL", "NETHERLANDS": "NL", "THE NETHERLANDS": "NL", "NIEDERLANDE": "NL", "HOLLAND": "NL",
    "CA": "CA", "CAN": "CA", "CANADA": "CA", "KANADA": "CA",
    "AU": "AU", "AUS": "AU", "AUSTRALIA": "AU", "AUSTRALIEN": "AU",
    "PL": "PL", "POL": "PL", "POLAND": "PL", "POLEN": "PL",
    "BE": "BE", "BEL": "BE", "BELGIUM": "BE", "BELGIEN": "BE",
    "SE": "SE", "SWE": "SE", "SWEDEN": "SE", "SCHWEDEN": "SE",
    "DK": "DK", "DNK": "DK", "DENMARK": "DK", "DÄNEMARK": "DK", "DAENEMARK": "DK",
    "NO": "NO", "NOR": "NO", "NORWAY": "NO", "NORWEGEN": "NO",
    "FI": "FI", "FIN": "FI", "FINLAND": "FI", "FINNLAND": "FI",
    "PT": "PT", "PRT": "PT", "PORTUGAL": "PT",
    "IE": "IE", "IRL": "IE", "IRELAND": "IE", "IRLAND": "IE",
    "GR": "GR", "GRC": "GR", "GREECE": "GR", "GRIECHENLAND": "GR",
    "TR": "TR", "TUR": "TR", "TURKEY": "TR", "TÜRKEI": "TR", "TUERKEI": "TR",
    "BR": "BR", "BRA": "BR", "BRAZIL": "BR", "BRASILIEN": "BR",
    "CN": "CN", "CHN": "CN", "CHINA": "CN",
    "JP": "JP", "JPN": "JP", "JAPAN": "JP",
    "IN": "IN", "IND": "IN", "INDIA": "IN", "INDIEN": "IN",
    "MX": "MX", "MEX": "MX", "MEXICO": "MX", "MEXIKO": "MX",
    "RU": "RU", "RUS": "RU", "RUSSIA": "RU", "RUSSLAND": "RU",
    "ZA": "ZA", "ZAF": "ZA", "SOUTH AFRICA": "ZA", "SÜDAFRIKA": "ZA", "SUEDAFRIKA": "ZA",
    "CZ": "CZ", "CZE": "CZ", "CZECH REPUBLIC": "CZ", "CZECHIA": "CZ", "TSCHECHIEN": "CZ",
    "HU": "HU", "HUN": "HU", "HUNGARY": "HU", "UNGARN": "HU",
    "RO": "RO", "ROU": "RO", "ROMANIA": "RO", "RUMÄNIEN": "RO", "RUMAENIEN": "RO",
    "LU": "LU", "LUX": "LU", "LUXEMBOURG": "LU", "LUXEMBURG": "LU"
}

def clean_country(val):
    if pd.isna(val) or val is None:
        return "UNKNOWN"
    s = str(val).strip().upper()
    if not s or s in ["NONE", "NAN", "NULL", "UNKNOWN", "?", "-", "N/A"]:
        return "UNKNOWN"
    return iso2_map.get(s, "UNKNOWN")

if "country" in df.columns:
    df["country"] = df["country"].apply(clean_country)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)