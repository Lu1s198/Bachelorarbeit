import pandas as pd
import numpy as np

df = pd.read_parquet("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r5/cleaning_medium/output.parquet")

country_map = {
    "GERMANY": "DE", "DEUTSCHLAND": "DE", "DE": "DE", "GER": "DE", "DEU": "DE",
    "USA": "US", "US": "US", "UNITED STATES": "US", "UNITED STATES OF AMERICA": "US",
    "VEREINIGTE STAATEN": "US", "VEREINIGTE STAATEN VON AMERIKA": "US", "USA.": "US",
    "UK": "GB", "UNITED KINGDOM": "GB", "GREAT BRITAIN": "GB", "GB": "GB",
    "GROSSBRITANNIEN": "GB", "GROßBRITANNIEN": "GB", "VEREINIGTES KOENIGREICH": "GB",
    "VEREINIGTES KÖNIGREICH": "GB", "ENGLAND": "GB",
    "FRANCE": "FR", "FRANKREICH": "FR", "FR": "FR", "FRA": "FR",
    "SPAIN": "ES", "SPANIEN": "ES", "ES": "ES", "ESP": "ES",
    "ITALY": "IT", "ITALIEN": "IT", "IT": "IT", "ITA": "IT",
    "NETHERLANDS": "NL", "NIEDERLANDE": "NL", "NL": "NL", "NLD": "NL", "HOLLAND": "NL",
    "BELGIUM": "BE", "BELGIEN": "BE", "BE": "BE", "BEL": "BE",
    "AUSTRIA": "AT", "OESTERREICH": "AT", "ÖSTERREICH": "AT", "AT": "AT", "AUT": "AT",
    "SWITZERLAND": "CH", "SCHWEIZ": "CH", "CH": "CH", "CHE": "CH",
    "POLAND": "PL", "POLEN": "PL", "PL": "PL", "POL": "POL"[:2],
    "PORTUGAL": "PT", "PT": "PT", "PRT": "PT",
    "SWEDEN": "SE", "SCHWEDEN": "SE", "SE": "SE", "SWE": "SE",
    "NORWAY": "NO", "NORWEGEN": "NO", "NO": "NO", "NOR": "NO",
    "DENMARK": "DK", "DAENEMARK": "DK", "DÄNEMARK": "DK", "DK": "DK", "DNK": "DK",
    "FINLAND": "FI", "FINNLAND": "FI", "FI": "FI", "FIN": "FI",
    "IRELAND": "IE", "IRLAND": "IE", "IE": "IE", "IRL": "IE",
    "GREECE": "GR", "GRIECHENLAND": "GR", "GR": "GR", "GRC": "GR",
    "CZECH REPUBLIC": "CZ", "TSCHECHIEN": "CZ", "TSCHECHISCHE REPUBLIK": "CZ", "CZ": "CZ", "CZE": "CZ",
    "SLOVAKIA": "SK", "SLOWAKEI": "SK", "SK": "SK", "SVK": "SK",
    "HUNGARY": "HU", "UNGARN": "HU", "HU": "HU", "HUN": "HU",
    "ROMANIA": "RO", "RUMAENIEN": "RO", "RUMÄNIEN": "RO", "RO": "RO", "ROU": "RO",
    "BULGARIA": "BG", "BULGARIEN": "BG", "BG": "BG", "BGR": "BG",
    "CROATIA": "HR", "KROATIEN": "HR", "HR": "HR", "HRV": "HR",
    "SLOVENIA": "SI", "SLOWENIEN": "SI", "SI": "SI", "SVN": "SI",
    "SERBIA": "RS", "SERBIEN": "RS", "RS": "RS", "SRB": "RS",
    "UKRAINE": "UA", "UA": "UA", "UKR": "UA",
    "RUSSIA": "RU", "RUSSLAND": "RU", "RU": "RU", "RUS": "RU",
    "TURKEY": "TR", "TUERKEI": "TR", "TÜRKEI": "TR", "TR": "TR", "TUR": "TR",
    "CHINA": "CN", "CN": "CN", "CHN": "CN",
    "JAPAN": "JP", "JP": "JP", "JPN": "JP",
    "INDIA": "IN", "INDIEN": "IN", "IN": "IN", "IND": "IN",
    "BRAZIL": "BR", "BRASILIEN": "BR", "BR": "BR", "BRA": "BR",
    "CANADA": "CA", "KANADA": "CA", "CA": "CA", "CAN": "CA",
    "AUSTRALIA": "AU", "AUSTRALIEN": "AU", "AU": "AU", "AUS": "AU",
    "MEXICO": "MX", "MEXIKO": "MX", "MX": "MX", "MEX": "MX",
    "SOUTH AFRICA": "ZA", "SUEDAFRIKA": "ZA", "SÜDAFRIKA": "ZA", "ZA": "ZA", "ZAF": "ZA",
    "SOUTH KOREA": "KR", "SUEDKOREA": "KR", "SÜDKOREA": "KR", "KR": "KR", "KOR": "KR",
    "NEW ZEALAND": "NZ", "NEUSEELAND": "NZ", "NZ": "NZ", "NZL": "NZ",
    "LUXEMBOURG": "LU", "LUXEMBURG": "LU", "LU": "LU", "LUX": "LU",
    "ICELAND": "IS", "ISLAND": "IS", "IS": "IS", "ISL": "IS",
    "ESTONIA": "EE", "ESTLAND": "EE", "EE": "EE", "EST": "EE",
    "LATVIA": "LV", "LETTLAND": "LV", "LV": "LV", "LVA": "LV",
    "LITHUANIA": "LT", "LITAUEN": "LT", "LT": "LT", "LTU": "LT",
    "CYPRUS": "CY", "ZYPERN": "CY", "CY": "CY", "CYP": "CY",
    "MALTA": "MT", "MT": "MT", "MLT": "MT",
}

def normalize_country(val):
    if pd.isna(val):
        return "UNKNOWN"
    s = str(val).strip().upper()
    s = s.replace(".", "").strip()
    if s in country_map:
        return country_map[s]
    return "UNKNOWN"

df["country"] = df["country"].apply(normalize_country)

df.to_parquet("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r5/cleaning_hard/output.parquet", index=False)