import pandas as pd
import numpy as np

df = pd.read_parquet("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/anthropic/cleaning_medium/output.parquet")

country_map = {
    "DE": "DE", "DEU": "DE", "GERMANY": "DE", "GERMAN": "DE", "DEUTSCHLAND": "DE",
    "ALLEMAGNE": "DE", "GER": "DE",
    "AT": "AT", "AUT": "AT", "AUSTRIA": "AT", "OESTERREICH": "AT", "ÖSTERREICH": "AT",
    "CH": "CH", "CHE": "CH", "SWITZERLAND": "CH", "SCHWEIZ": "CH", "SUISSE": "CH",
    "US": "US", "USA": "US", "UNITEDSTATES": "US", "UNITEDSTATESOFAMERICA": "US",
    "VEREINIGTESTAATEN": "US", "VEREINIGTESTAATENVONAMERIKA": "US", "AMERICA": "US",
    "GB": "GB", "GBR": "GB", "UK": "GB", "UNITEDKINGDOM": "GB", "GROSSBRITANNIEN": "GB",
    "GROßBRITANNIEN": "GB", "ENGLAND": "GB", "GREATBRITAIN": "GB",
    "FR": "FR", "FRA": "FR", "FRANCE": "FR", "FRANKREICH": "FR",
    "IT": "IT", "ITA": "IT", "ITALY": "IT", "ITALIEN": "IT", "ITALIA": "IT",
    "ES": "ES", "ESP": "ES", "SPAIN": "ES", "SPANIEN": "ES", "ESPANA": "ES", "ESPAÑA": "ES",
    "NL": "NL", "NLD": "NL", "NETHERLANDS": "NL", "NIEDERLANDE": "NL", "HOLLAND": "NL",
    "BE": "BE", "BEL": "BE", "BELGIUM": "BE", "BELGIEN": "BE", "BELGIQUE": "BE",
    "PL": "PL", "POL": "PL", "POLAND": "PL", "POLEN": "PL", "POLSKA": "PL",
    "PT": "PT", "PRT": "PT", "PORTUGAL": "PT",
    "SE": "SE", "SWE": "SE", "SWEDEN": "SE", "SCHWEDEN": "SE",
    "NO": "NO", "NOR": "NO", "NORWAY": "NO", "NORWEGEN": "NO",
    "DK": "DK", "DNK": "DK", "DENMARK": "DK", "DAENEMARK": "DK", "DÄNEMARK": "DK",
    "FI": "FI", "FIN": "FI", "FINLAND": "FI", "FINNLAND": "FI",
    "IE": "IE", "IRL": "IE", "IRELAND": "IE", "IRLAND": "IE",
    "GR": "GR", "GRC": "GR", "GREECE": "GR", "GRIECHENLAND": "GR",
    "CZ": "CZ", "CZE": "CZ", "CZECHREPUBLIC": "CZ", "TSCHECHIEN": "CZ", "TSCHECHISCHEREPUBLIK": "CZ",
    "SK": "SK", "SVK": "SK", "SLOVAKIA": "SK", "SLOWAKEI": "SK",
    "HU": "HU", "HUN": "HU", "HUNGARY": "HU", "UNGARN": "HU",
    "RO": "RO", "ROU": "RO", "ROMANIA": "RO", "RUMAENIEN": "RO", "RUMÄNIEN": "RO",
    "BG": "BG", "BGR": "BG", "BULGARIA": "BG", "BULGARIEN": "BG",
    "HR": "HR", "HRV": "HR", "CROATIA": "HR", "KROATIEN": "HR",
    "SI": "SI", "SVN": "SI", "SLOVENIA": "SI", "SLOWENIEN": "SI",
    "CH2": "CH",
    "LU": "LU", "LUX": "LU", "LUXEMBOURG": "LU", "LUXEMBURG": "LU",
    "LI": "LI", "LIE": "LI", "LIECHTENSTEIN": "LI",
    "RU": "RU", "RUS": "RU", "RUSSIA": "RU", "RUSSLAND": "RU", "RUSSIANFEDERATION": "RU",
    "CN": "CN", "CHN": "CN", "CHINA": "CN",
    "JP": "JP", "JPN": "JP", "JAPAN": "JP",
    "IN": "IN", "IND": "IN", "INDIA": "IN", "INDIEN": "IN",
    "BR": "BR", "BRA": "BR", "BRAZIL": "BR", "BRASILIEN": "BR",
    "CA": "CA", "CAN": "CA", "CANADA": "CA", "KANADA": "CA",
    "AU": "AU", "AUS": "AU", "AUSTRALIA": "AU", "AUSTRALIEN": "AU",
    "MX": "MX", "MEX": "MX", "MEXICO": "MX", "MEXIKO": "MX",
    "AR": "AR", "ARG": "AR", "ARGENTINA": "AR", "ARGENTINIEN": "AR",
    "ZA": "ZA", "ZAF": "ZA", "SOUTHAFRICA": "ZA", "SUEDAFRIKA": "ZA", "SÜDAFRIKA": "ZA",
    "EG": "EG", "EGY": "EG", "EGYPT": "EG", "AEGYPTEN": "EG", "ÄGYPTEN": "EG",
    "TR": "TR", "TUR": "TR", "TURKEY": "TR", "TUERKEI": "TR", "TÜRKEI": "TR",
    "UA": "UA", "UKR": "UA", "UKRAINE": "UA",
    "KR": "KR", "KOR": "KR", "SOUTHKOREA": "KR", "SUEDKOREA": "KR", "SÜDKOREA": "KR",
    "NZ": "NZ", "NZL": "NZ", "NEWZEALAND": "NZ", "NEUSEELAND": "NZ",
    "IS": "IS", "ISL": "IS", "ICELAND": "IS", "ISLAND": "IS",
    "LT": "LT", "LTU": "LT", "LITHUANIA": "LT", "LITAUEN": "LT",
    "LV": "LV", "LVA": "LV", "LATVIA": "LV", "LETTLAND": "LV",
    "EE": "EE", "EST": "EE", "ESTONIA": "EE", "ESTLAND": "EE",
    "CY": "CY", "CYP": "CY", "CYPRUS": "CY", "ZYPERN": "CY",
    "MT": "MT", "MLT": "MT", "MALTA": "MT",
}

def normalize_country(val):
    if pd.isna(val):
        return "UNKNOWN"
    s = str(val).strip().upper()
    s = s.replace(".", "").replace("-", "").replace("_", "").replace(" ", "")
    if s in country_map:
        return country_map[s]
    return "UNKNOWN"

df["country"] = df["country"].apply(normalize_country)

df.to_parquet("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/anthropic/cleaning_hard/output.parquet", index=False)