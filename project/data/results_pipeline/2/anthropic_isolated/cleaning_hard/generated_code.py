import pandas as pd
import numpy as np

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_medium/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_isolated/cleaning_hard/output.parquet"

df = pd.read_parquet(input_path)

country_map = {
    "GERMANY": "DE", "DEUTSCHLAND": "DE", "DE": "DE", "GER": "DE", "DEU": "DE",
    "USA": "US", "US": "US", "UNITED STATES": "US", "UNITED STATES OF AMERICA": "US",
    "VEREINIGTE STAATEN": "US", "VEREINIGTE STAATEN VON AMERIKA": "US", "AMERICA": "US",
    "UK": "GB", "UNITED KINGDOM": "GB", "GREAT BRITAIN": "GB", "GROSSBRITANNIEN": "GB",
    "GB": "GB", "GBR": "GB", "VEREINIGTES KOENIGREICH": "GB", "VEREINIGTES KÖNIGREICH": "GB",
    "ENGLAND": "GB",
    "FRANCE": "FR", "FRANKREICH": "FR", "FR": "FR", "FRA": "FR",
    "SPAIN": "ES", "SPANIEN": "ES", "ES": "ES", "ESP": "ES",
    "ITALY": "IT", "ITALIEN": "IT", "IT": "IT", "ITA": "IT",
    "AUSTRIA": "AT", "OESTERREICH": "AT", "ÖSTERREICH": "AT", "AT": "AT", "AUT": "AT",
    "SWITZERLAND": "CH", "SCHWEIZ": "CH", "CH": "CH", "CHE": "CH",
    "NETHERLANDS": "NL", "NIEDERLANDE": "NL", "NL": "NL", "NLD": "NL", "HOLLAND": "NL",
    "BELGIUM": "BE", "BELGIEN": "BE", "BE": "BE", "BEL": "BE",
    "POLAND": "PL", "POLEN": "PL", "PL": "PL", "POL": "POL"[:2],
    "PORTUGAL": "PT", "PT": "PT", "PRT": "PT",
    "SWEDEN": "SE", "SCHWEDEN": "SE", "SE": "SE", "SWE": "SE",
    "NORWAY": "NO", "NORWEGEN": "NO", "NO": "NO", "NOR": "NO",
    "DENMARK": "DK", "DAENEMARK": "DK", "DÄNEMARK": "DK", "DK": "DK", "DNK": "DK",
    "FINLAND": "FI", "FINNLAND": "FI", "FI": "FI", "FIN": "FI",
    "GREECE": "GR", "GRIECHENLAND": "GR", "GR": "GR", "GRC": "GR",
    "IRELAND": "IE", "IRLAND": "IE", "IE": "IE", "IRL": "IE",
    "LUXEMBOURG": "LU", "LUXEMBURG": "LU", "LU": "LU", "LUX": "LU",
    "CZECH REPUBLIC": "CZ", "TSCHECHIEN": "CZ", "CZ": "CZ", "CZE": "CZ",
    "SLOVAKIA": "SK", "SLOWAKEI": "SK", "SK": "SK", "SVK": "SK",
    "HUNGARY": "HU", "UNGARN": "HU", "HU": "HU", "HUN": "HU",
    "ROMANIA": "RO", "RUMAENIEN": "RO", "RUMÄNIEN": "RO", "RO": "RO", "ROU": "RO",
    "BULGARIA": "BG", "BULGARIEN": "BG", "BG": "BG", "BGR": "BG",
    "CROATIA": "HR", "KROATIEN": "HR", "HR": "HR", "HRV": "HR",
    "SLOVENIA": "SI", "SLOWENIEN": "SI", "SI": "SI", "SVN": "SI",
    "ESTONIA": "EE", "ESTLAND": "EE", "EE": "EE", "EST": "EE",
    "LATVIA": "LV", "LETTLAND": "LV", "LV": "LV", "LVA": "LV",
    "LITHUANIA": "LT", "LITAUEN": "LT", "LT": "LT", "LTU": "LT",
    "RUSSIA": "RU", "RUSSLAND": "RU", "RU": "RU", "RUS": "RU",
    "UKRAINE": "UA", "UA": "UA", "UKR": "UA",
    "TURKEY": "TR", "TUERKEI": "TR", "TÜRKEI": "TR", "TR": "TR", "TUR": "TR",
    "CHINA": "CN", "CN": "CN", "CHN": "CN",
    "JAPAN": "JP", "JP": "JP", "JPN": "JP",
    "INDIA": "IN", "INDIEN": "IN", "IN": "IN", "IND": "IN",
    "CANADA": "CA", "KANADA": "CA", "CA": "CA", "CAN": "CA",
    "AUSTRALIA": "AU", "AUSTRALIEN": "AU", "AU": "AU", "AUS": "AU",
    "BRAZIL": "BR", "BRASILIEN": "BR", "BR": "BR", "BRA": "BR",
    "MEXICO": "MX", "MEXIKO": "MX", "MX": "MX", "MEX": "MX",
    "SOUTH AFRICA": "ZA", "SUEDAFRIKA": "ZA", "SÜDAFRIKA": "ZA", "ZA": "ZA", "ZAF": "ZA",
    "SOUTH KOREA": "KR", "SUEDKOREA": "KR", "SÜDKOREA": "KR", "KR": "KR", "KOR": "KR",
    "NEW ZEALAND": "NZ", "NEUSEELAND": "NZ", "NZ": "NZ", "NZL": "NZ",
    "ARGENTINA": "AR", "ARGENTINIEN": "AR", "AR": "AR", "ARG": "AR",
    "CHILE": "CL", "CL": "CL", "CHL": "CL",
    "COLOMBIA": "CO", "KOLUMBIEN": "CO", "CO": "CO", "COL": "CO",
    "EGYPT": "EG", "AEGYPTEN": "EG", "ÄGYPTEN": "EG", "EG": "EG", "EGY": "EG",
    "ISRAEL": "IL", "IL": "IL", "ISR": "IL",
    "SAUDI ARABIA": "SA", "SAUDI-ARABIEN": "SA", "SA": "SA", "SAU": "SA",
    "UNITED ARAB EMIRATES": "AE", "VEREINIGTE ARABISCHE EMIRATE": "AE", "AE": "AE", "ARE": "AE",
    "THAILAND": "TH", "TH": "TH", "THA": "TH",
    "VIETNAM": "VN", "VN": "VN", "VNM": "VN",
    "INDONESIA": "ID", "INDONESIEN": "ID", "ID": "ID", "IDN": "ID",
    "MALAYSIA": "MY", "MY": "MY", "MYS": "MY",
    "PHILIPPINES": "PH", "PHILIPPINEN": "PH", "PH": "PH", "PHL": "PH",
    "SINGAPORE": "SG", "SINGAPUR": "SG", "SG": "SG", "SGP": "SG",
    "PAKISTAN": "PK", "PK": "PK", "PAK": "PK",
    "NIGERIA": "NG", "NG": "NG", "NGA": "NG",
    "KENYA": "KE", "KENIA": "KE", "KE": "KE", "KEN": "KE",
    "MOROCCO": "MA", "MAROKKO": "MA", "MA": "MA", "MAR": "MA",
    "SERBIA": "RS", "SERBIEN": "RS", "RS": "RS", "SRB": "RS",
    "ICELAND": "IS", "ISLAND": "IS", "IS": "IS", "ISL": "IS",
    "CYPRUS": "CY", "ZYPERN": "CY", "CY": "CY", "CYP": "CY",
    "MALTA": "MT", "MT": "MT", "MLT": "MT",
}


def normalize_country(val):
    if pd.isna(val):
        return "UNKNOWN"
    s = str(val).strip().upper()
    s = s.replace(".", "").replace("_", " ").replace("-", " ")
    s = " ".join(s.split())
    if s in country_map:
        return country_map[s]
    s_nospace = s.replace(" ", "")
    if s_nospace in country_map:
        return country_map[s_nospace]
    return "UNKNOWN"


df["country"] = df["country"].apply(normalize_country)

df.to_parquet(output_path, index=False)