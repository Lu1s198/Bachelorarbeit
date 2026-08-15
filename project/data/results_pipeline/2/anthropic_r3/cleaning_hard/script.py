import pandas as pd
import numpy as np

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r3/cleaning_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r3/cleaning_hard/output.parquet"

df = pd.read_parquet(input_path)

country_map = {
    "GERMANY": "DE", "DEUTSCHLAND": "DE", "DE": "DE", "GER": "DE", "DEU": "DE", "D": "DE",
    "AUSTRIA": "AT", "OESTERREICH": "AT", "ÖSTERREICH": "AT", "AT": "AT", "AUT": "AT", "A": "AT",
    "SWITZERLAND": "CH", "SCHWEIZ": "CH", "CH": "CH", "CHE": "CH", "SUISSE": "CH", "SVIZZERA": "CH",
    "UNITED STATES": "US", "UNITED STATES OF AMERICA": "US", "USA": "US", "US": "US", "VEREINIGTE STAATEN": "US", "AMERICA": "US",
    "UNITED KINGDOM": "GB", "GREAT BRITAIN": "GB", "UK": "GB", "GB": "GB", "GBR": "GB", "GROSSBRITANNIEN": "GB", "GROßBRITANNIEN": "GB", "ENGLAND": "GB", "VEREINIGTES KOENIGREICH": "GB", "VEREINIGTES KÖNIGREICH": "GB",
    "FRANCE": "FR", "FRANKREICH": "FR", "FR": "FR", "FRA": "FR",
    "SPAIN": "ES", "SPANIEN": "ES", "ES": "ES", "ESP": "ES",
    "ITALY": "IT", "ITALIEN": "IT", "IT": "IT", "ITA": "IT",
    "NETHERLANDS": "NL", "NIEDERLANDE": "NL", "NL": "NL", "NLD": "NL", "HOLLAND": "NL",
    "BELGIUM": "BE", "BELGIEN": "BE", "BE": "BE", "BEL": "BE",
    "LUXEMBOURG": "LU", "LUXEMBURG": "LU", "LU": "LU", "LUX": "LU",
    "POLAND": "PL", "POLEN": "PL", "PL": "PL", "POL": "PL",
    "CZECH REPUBLIC": "CZ", "TSCHECHIEN": "CZ", "CZ": "CZ", "CZE": "CZ", "CZECHIA": "CZ",
    "SLOVAKIA": "SK", "SLOWAKEI": "SK", "SK": "SK", "SVK": "SK",
    "HUNGARY": "HU", "UNGARN": "HU", "HU": "HU", "HUN": "HU",
    "PORTUGAL": "PT", "PT": "PT", "PRT": "PT",
    "DENMARK": "DK", "DAENEMARK": "DK", "DÄNEMARK": "DK", "DK": "DK", "DNK": "DK",
    "SWEDEN": "SE", "SCHWEDEN": "SE", "SE": "SE", "SWE": "SE",
    "NORWAY": "NO", "NORWEGEN": "NO", "NO": "NO", "NOR": "NO",
    "FINLAND": "FI", "FINNLAND": "FI", "FI": "FI", "FIN": "FI",
    "IRELAND": "IE", "IRLAND": "IE", "IE": "IE", "IRL": "IE",
    "GREECE": "GR", "GRIECHENLAND": "GR", "GR": "GR", "GRC": "GR",
    "TURKEY": "TR", "TUERKEI": "TR", "TÜRKEI": "TR", "TR": "TR", "TUR": "TR",
    "RUSSIA": "RU", "RUSSLAND": "RU", "RU": "RU", "RUS": "RU",
    "UKRAINE": "UA", "UA": "UA", "UKR": "UA",
    "CHINA": "CN", "CN": "CN", "CHN": "CN",
    "JAPAN": "JP", "JP": "JP", "JPN": "JP",
    "SOUTH KOREA": "KR", "SUEDKOREA": "KR", "SÜDKOREA": "KR", "KR": "KR", "KOR": "KR",
    "INDIA": "IN", "INDIEN": "IN", "IN": "IN", "IND": "IN",
    "BRAZIL": "BR", "BRASILIEN": "BR", "BR": "BR", "BRA": "BR",
    "CANADA": "CA", "KANADA": "CA", "CA": "CA", "CAN": "CA",
    "AUSTRALIA": "AU", "AUSTRALIEN": "AU", "AU": "AU", "AUS": "AU",
    "MEXICO": "MX", "MEXIKO": "MX", "MX": "MX", "MEX": "MX",
    "ARGENTINA": "AR", "ARGENTINIEN": "AR", "AR": "AR", "ARG": "AR",
    "SOUTH AFRICA": "ZA", "SUEDAFRIKA": "ZA", "SÜDAFRIKA": "ZA", "ZA": "ZA", "ZAF": "ZA",
    "EGYPT": "EG", "AEGYPTEN": "EG", "ÄGYPTEN": "EG", "EG": "EG", "EGY": "EG",
    "CROATIA": "HR", "KROATIEN": "HR", "HR": "HR", "HRV": "HR",
    "SLOVENIA": "SI", "SLOWENIEN": "SI", "SI": "SI", "SVN": "SI",
    "ROMANIA": "RO", "RUMAENIEN": "RO", "RUMÄNIEN": "RO", "RO": "RO", "ROU": "RO",
    "BULGARIA": "BG", "BULGARIEN": "BG", "BG": "BG", "BGR": "BG",
    "SERBIA": "RS", "SERBIEN": "RS", "RS": "RS", "SRB": "RS",
    "ICELAND": "IS", "ISLAND": "IS", "IS": "IS", "ISL": "IS",
    "NEW ZEALAND": "NZ", "NEUSEELAND": "NZ", "NZ": "NZ", "NZL": "NZ",
    "THAILAND": "TH", "TH": "TH", "THA": "TH",
    "VIETNAM": "VN", "VN": "VN", "VNM": "VN",
    "INDONESIA": "ID", "INDONESIEN": "ID", "ID": "ID", "IDN": "ID",
    "MALAYSIA": "MY", "MY": "MY", "MYS": "MY",
    "SINGAPORE": "SG", "SINGAPUR": "SG", "SG": "SG", "SGP": "SG",
    "PHILIPPINES": "PH", "PHILIPPINEN": "PH", "PH": "PH", "PHL": "PH",
    "PAKISTAN": "PK", "PK": "PK", "PAK": "PK",
    "ISRAEL": "IL", "IL": "IL", "ISR": "IL",
    "SAUDI ARABIA": "SA", "SAUDI ARABIEN": "SA", "SA": "SA", "SAU": "SA",
    "UNITED ARAB EMIRATES": "AE", "VEREINIGTE ARABISCHE EMIRATE": "AE", "AE": "AE", "ARE": "AE", "UAE": "AE",
    "CHILE": "CL", "CL": "CL", "CHL": "CL",
    "COLOMBIA": "CO", "KOLUMBIEN": "CO", "CO": "CO", "COL": "CO",
    "PERU": "PE", "PE": "PE", "PER": "PE",
    "VENEZUELA": "VE", "VE": "VE", "VEN": "VE",
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
    s = s.replace(".", "")
    if s in country_map:
        return country_map[s]
    return "UNKNOWN"

df["country"] = df["country"].apply(normalize_country)

df.to_parquet(output_path, index=False)