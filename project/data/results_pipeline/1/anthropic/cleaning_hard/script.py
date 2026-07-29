import pandas as pd
import numpy as np

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/cleaning_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/cleaning_hard/output.parquet"

df = pd.read_parquet(input_path)

country_map = {
    "GERMANY": "DE", "DEUTSCHLAND": "DE", "DE": "DE", "GER": "DE",
    "UNITED STATES": "US", "UNITED STATES OF AMERICA": "US", "USA": "US", "US": "US",
    "UNITED KINGDOM": "GB", "UK": "GB", "GB": "GB", "GREAT BRITAIN": "GB", "ENGLAND": "GB",
    "FRANCE": "FR", "FR": "FR",
    "SPAIN": "ES", "ES": "ES", "ESPANA": "ES", "ESPAÑA": "ES",
    "ITALY": "IT", "IT": "IT", "ITALIA": "IT",
    "NETHERLANDS": "NL", "NL": "NL", "HOLLAND": "NL", "THE NETHERLANDS": "NL",
    "BELGIUM": "BE", "BE": "BE",
    "AUSTRIA": "AT", "AT": "AT", "OSTERREICH": "AT", "ÖSTERREICH": "AT",
    "SWITZERLAND": "CH", "CH": "CH", "SCHWEIZ": "CH",
    "POLAND": "PL", "PL": "PL", "POLSKA": "PL",
    "PORTUGAL": "PT", "PT": "PT",
    "SWEDEN": "SE", "SE": "SE",
    "NORWAY": "NO", "NO": "NO",
    "DENMARK": "DK", "DK": "DK",
    "FINLAND": "FI", "FI": "FI",
    "IRELAND": "IE", "IE": "IE",
    "GREECE": "GR", "GR": "GR",
    "CZECH REPUBLIC": "CZ", "CZ": "CZ", "CZECHIA": "CZ",
    "HUNGARY": "HU", "HU": "HU",
    "ROMANIA": "RO", "RO": "RO",
    "BULGARIA": "BG", "BG": "BG",
    "SLOVAKIA": "SK", "SK": "SK",
    "SLOVENIA": "SI", "SI": "SI",
    "CROATIA": "HR", "HR": "HR",
    "ESTONIA": "EE", "EE": "EE",
    "LATVIA": "LV", "LV": "LV",
    "LITHUANIA": "LT", "LT": "LT",
    "LUXEMBOURG": "LU", "LU": "LU",
    "MALTA": "MT", "MT": "MT",
    "CYPRUS": "CY", "CY": "CY",
    "ICELAND": "IS", "IS": "IS",
    "RUSSIA": "RU", "RU": "RU", "RUSSIAN FEDERATION": "RU",
    "UKRAINE": "UA", "UA": "UA",
    "TURKEY": "TR", "TR": "TR", "TURKIYE": "TR", "TÜRKIYE": "TR",
    "CHINA": "CN", "CN": "CN",
    "JAPAN": "JP", "JP": "JP",
    "SOUTH KOREA": "KR", "KR": "KR", "KOREA": "KR", "REPUBLIC OF KOREA": "KR",
    "INDIA": "IN", "IN": "IN",
    "AUSTRALIA": "AU", "AU": "AU",
    "NEW ZEALAND": "NZ", "NZ": "NZ",
    "CANADA": "CA", "CA": "CA",
    "MEXICO": "MX", "MX": "MX",
    "BRAZIL": "BR", "BR": "BR", "BRASIL": "BR",
    "ARGENTINA": "AR", "AR": "AR",
    "CHILE": "CL", "CL": "CL",
    "COLOMBIA": "CO", "CO": "CO",
    "PERU": "PE", "PE": "PE",
    "SOUTH AFRICA": "ZA", "ZA": "ZA",
    "EGYPT": "EG", "EG": "EG",
    "NIGERIA": "NG", "NG": "NG",
    "KENYA": "KE", "KE": "KE",
    "ISRAEL": "IL", "IL": "IL",
    "SAUDI ARABIA": "SA", "SA": "SA",
    "UNITED ARAB EMIRATES": "AE", "AE": "AE", "UAE": "AE",
    "INDONESIA": "ID", "ID": "ID",
    "MALAYSIA": "MY", "MY": "MY",
    "SINGAPORE": "SG", "SG": "SG",
    "THAILAND": "TH", "TH": "TH",
    "VIETNAM": "VN", "VN": "VN",
    "PHILIPPINES": "PH", "PH": "PH",
    "PAKISTAN": "PK", "PK": "PK",
    "BANGLADESH": "BD", "BD": "BD",
}

def normalize_country(val):
    if pd.isna(val):
        return "UNKNOWN"
    s = str(val).strip().upper()
    s = s.replace(".", "")
    if s == "":
        return "UNKNOWN"
    if s in country_map:
        return country_map[s]
    return "UNKNOWN"

df["country"] = df["country"].apply(normalize_country)

df.to_parquet(output_path, index=False)