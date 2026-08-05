import pandas as pd
import numpy as np

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/cleaning_medium/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/cleaning_hard/output.parquet"

df = pd.read_parquet(input_path)

country_map = {
    "DE": "DE", "DEU": "DE", "GER": "DE", "GERMANY": "DE", "DEUTSCHLAND": "DE",
    "AT": "AT", "AUT": "AT", "AUSTRIA": "AT", "OESTERREICH": "AT", "ÖSTERREICH": "AT",
    "CH": "CH", "CHE": "CH", "SWITZERLAND": "CH", "SCHWEIZ": "CH", "SUISSE": "CH",
    "US": "US", "USA": "US", "UNITEDSTATES": "US", "UNITEDSTATESOFAMERICA": "US",
    "VEREINIGTESTAATEN": "US", "VEREINIGTESTAATENVONAMERIKA": "US",
    "GB": "GB", "UK": "GB", "GBR": "GB", "UNITEDKINGDOM": "GB", "GREATBRITAIN": "GB",
    "GROSSBRITANNIEN": "GB", "GROßBRITANNIEN": "GB", "VEREINIGTESKOENIGREICH": "GB",
    "VEREINIGTESKÖNIGREICH": "GB", "ENGLAND": "GB",
    "FR": "FR", "FRA": "FR", "FRANCE": "FR", "FRANKREICH": "FR",
    "IT": "IT", "ITA": "IT", "ITALY": "IT", "ITALIEN": "IT",
    "ES": "ES", "ESP": "ES", "SPAIN": "ES", "SPANIEN": "ES",
    "PT": "PT", "PRT": "PT", "PORTUGAL": "PT",
    "NL": "NL", "NLD": "NL", "NETHERLANDS": "NL", "NIEDERLANDE": "NL", "HOLLAND": "NL",
    "BE": "BE", "BEL": "BE", "BELGIUM": "BE", "BELGIEN": "BE",
    "LU": "LU", "LUX": "LU", "LUXEMBOURG": "LU", "LUXEMBURG": "LU",
    "PL": "PL", "POL": "PL", "POLAND": "PL", "POLEN": "PL",
    "CZ": "CZ", "CZE": "CZ", "CZECHREPUBLIC": "CZ", "TSCHECHIEN": "CZ", "TSCHECHISCHEREPUBLIK": "CZ",
    "SK": "SK", "SVK": "SK", "SLOVAKIA": "SK", "SLOWAKEI": "SK",
    "HU": "HU", "HUN": "HU", "HUNGARY": "HU", "UNGARN": "HU",
    "DK": "DK", "DNK": "DK", "DENMARK": "DK", "DAENEMARK": "DK", "DÄNEMARK": "DK",
    "SE": "SE", "SWE": "SE", "SWEDEN": "SE", "SCHWEDEN": "SE",
    "NO": "NO", "NOR": "NO", "NORWAY": "NO", "NORWEGEN": "NO",
    "FI": "FI", "FIN": "FI", "FINLAND": "FI", "FINNLAND": "FI",
    "IE": "IE", "IRL": "IE", "IRELAND": "IE", "IRLAND": "IE",
    "GR": "GR", "GRC": "GR", "GREECE": "GR", "GRIECHENLAND": "GR",
    "RU": "RU", "RUS": "RU", "RUSSIA": "RU", "RUSSLAND": "RU", "RUSSIANFEDERATION": "RU",
    "UA": "UA", "UKR": "UA", "UKRAINE": "UA",
    "TR": "TR", "TUR": "TR", "TURKEY": "TR", "TUERKEI": "TR", "TÜRKEI": "TR",
    "CN": "CN", "CHN": "CN", "CHINA": "CN",
    "JP": "JP", "JPN": "JP", "JAPAN": "JP",
    "KR": "KR", "KOR": "KR", "SOUTHKOREA": "KR", "SUEDKOREA": "KR", "SÜDKOREA": "KR",
    "IN": "IN", "IND": "IN", "INDIA": "IN", "INDIEN": "IN",
    "BR": "BR", "BRA": "BR", "BRAZIL": "BR", "BRASILIEN": "BR",
    "CA": "CA", "CAN": "CA", "CANADA": "CA", "KANADA": "CA",
    "MX": "MX", "MEX": "MX", "MEXICO": "MX", "MEXIKO": "MX",
    "AU": "AU", "AUS": "AU", "AUSTRALIA": "AU", "AUSTRALIEN": "AU",
    "NZ": "NZ", "NZL": "NZ", "NEWZEALAND": "NZ", "NEUSEELAND": "NZ",
    "ZA": "ZA", "ZAF": "ZA", "SOUTHAFRICA": "ZA", "SUEDAFRIKA": "ZA", "SÜDAFRIKA": "ZA",
    "EG": "EG", "EGY": "EG", "EGYPT": "EG", "AEGYPTEN": "EG", "ÄGYPTEN": "EG",
    "AR": "AR", "ARG": "AR", "ARGENTINA": "AR", "ARGENTINIEN": "AR",
    "CL": "CL", "CHL": "CL", "CHILE": "CL",
    "CO": "CO", "COL": "CO", "COLOMBIA": "CO", "KOLUMBIEN": "CO",
    "PE": "PE", "PER": "PE", "PERU": "PE",
    "IL": "IL", "ISR": "IL", "ISRAEL": "IL",
    "SA": "SA", "SAU": "SA", "SAUDIARABIA": "SA", "SAUDIARABIEN": "SA",
    "AE": "AE", "ARE": "AE", "UNITEDARABEMIRATES": "AE", "VEREINIGTEARABISCHEEMIRATE": "AE",
    "SG": "SG", "SGP": "SG", "SINGAPORE": "SG", "SINGAPUR": "SG",
    "MY": "MY", "MYS": "MY", "MALAYSIA": "MY",
    "TH": "TH", "THA": "TH", "THAILAND": "TH",
    "ID": "ID", "IDN": "ID", "INDONESIA": "ID", "INDONESIEN": "ID",
    "PH": "PH", "PHL": "PH", "PHILIPPINES": "PH", "PHILIPPINEN": "PH",
    "VN": "VN", "VNM": "VN", "VIETNAM": "VN",
    "PK": "PK", "PAK": "PK", "PAKISTAN": "PK",
    "BD": "BD", "BGD": "BD", "BANGLADESH": "BD",
    "RO": "RO", "ROU": "RO", "ROMANIA": "RO", "RUMAENIEN": "RO", "RUMÄNIEN": "RO",
    "BG": "BG", "BGR": "BG", "BULGARIA": "BG", "BULGARIEN": "BG",
    "HR": "HR", "HRV": "HR", "CROATIA": "HR", "KROATIEN": "HR",
    "RS": "RS", "SRB": "RS", "SERBIA": "RS", "SERBIEN": "RS",
    "SI": "SI", "SVN": "SI", "SLOVENIA": "SI", "SLOWENIEN": "SI",
    "LT": "LT", "LTU": "LT", "LITHUANIA": "LT", "LITAUEN": "LT",
    "LV": "LV", "LVA": "LV", "LATVIA": "LV", "LETTLAND": "LV",
    "EE": "EE", "EST": "EE", "ESTONIA": "EE", "ESTLAND": "EE",
    "IS": "IS", "ISL": "IS", "ICELAND": "IS", "ISLAND": "IS",
    "CY": "CY", "CYP": "CY", "CYPRUS": "CY", "ZYPERN": "CY",
    "MT": "MT", "MLT": "MT", "MALTA": "MT",
    "LI": "LI", "LIE": "LI", "LIECHTENSTEIN": "LI",
}

def normalize_country(val):
    if pd.isna(val):
        return "UNKNOWN"
    s = str(val).strip().upper()
    s = s.replace(".", "").replace("-", "").replace(" ", "").replace("_", "")
    if s in country_map:
        return country_map[s]
    return "UNKNOWN"

df["country"] = df["country"].apply(normalize_country)

df.to_parquet(output_path, index=False)