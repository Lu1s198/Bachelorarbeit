import pandas as pd
import numpy as np
import os

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_isolated_r3/cleaning_hard/output.parquet"

df = pd.read_parquet(input_path)

country_map = {
    "DE": "DE", "DEU": "DE", "GER": "DE", "GERMANY": "DE", "DEUTSCHLAND": "DE", "ALLEMAGNE": "DE",
    "AT": "AT", "AUT": "AT", "AUSTRIA": "AT", "OESTERREICH": "AT", "ÖSTERREICH": "AT",
    "CH": "CH", "CHE": "CH", "SWITZERLAND": "CH", "SCHWEIZ": "CH", "SUISSE": "CH",
    "US": "US", "USA": "US", "UNITEDSTATES": "US", "UNITEDSTATESOFAMERICA": "US", "VEREINIGTESTAATEN": "US", "VEREINIGTESTAATENVONAMERIKA": "US",
    "GB": "GB", "UK": "GB", "GBR": "GB", "UNITEDKINGDOM": "GB", "GROSSBRITANNIEN": "GB", "GROßBRITANNIEN": "GB", "VEREINIGTESKOENIGREICH": "GB", "VEREINIGTESKÖNIGREICH": "GB",
    "FR": "FR", "FRA": "FR", "FRANCE": "FR", "FRANKREICH": "FR",
    "ES": "ES", "ESP": "ES", "SPAIN": "ES", "SPANIEN": "ES",
    "IT": "IT", "ITA": "IT", "ITALY": "IT", "ITALIEN": "IT",
    "NL": "NL", "NLD": "NL", "NETHERLANDS": "NL", "NIEDERLANDE": "NL", "HOLLAND": "NL",
    "BE": "BE", "BEL": "BE", "BELGIUM": "BE", "BELGIEN": "BE",
    "PL": "PL", "POL": "PL", "POLAND": "PL", "POLEN": "PL",
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
    "RS": "RS", "SRB": "RS", "SERBIA": "RS", "SERBIEN": "RS",
    "CH2": "CH",
    "LU": "LU", "LUX": "LU", "LUXEMBOURG": "LU", "LUXEMBURG": "LU",
    "LI": "LI", "LIE": "LI", "LIECHTENSTEIN": "LI",
    "IS": "IS", "ISL": "IS", "ICELAND": "IS", "ISLAND": "IS",
    "MT": "MT", "MLT": "MT", "MALTA": "MT",
    "CY": "CY", "CYP": "CY", "CYPRUS": "CY", "ZYPERN": "CY",
    "EE": "EE", "EST": "EE", "ESTONIA": "EE", "ESTLAND": "EE",
    "LV": "LV", "LVA": "LV", "LATVIA": "LV", "LETTLAND": "LV",
    "LT": "LT", "LTU": "LT", "LITHUANIA": "LT", "LITAUEN": "LT",
    "RU": "RU", "RUS": "RU", "RUSSIA": "RU", "RUSSLAND": "RU", "RUSSIANFEDERATION": "RU",
    "UA": "UA", "UKR": "UA", "UKRAINE": "UA",
    "BY": "BY", "BLR": "BY", "BELARUS": "BY", "WEISSRUSSLAND": "BY", "WEIßRUSSLAND": "BY",
    "TR": "TR", "TUR": "TR", "TURKEY": "TR", "TUERKEI": "TR", "TÜRKEI": "TR",
    "CA": "CA", "CAN": "CA", "CANADA": "CA", "KANADA": "CA",
    "MX": "MX", "MEX": "MX", "MEXICO": "MX", "MEXIKO": "MX",
    "BR": "BR", "BRA": "BR", "BRAZIL": "BR", "BRASILIEN": "BR",
    "AR": "AR", "ARG": "AR", "ARGENTINA": "AR", "ARGENTINIEN": "AR",
    "CL": "CL", "CHL": "CL", "CHILE": "CL",
    "CO": "CO", "COL": "CO", "COLOMBIA": "CO", "KOLUMBIEN": "CO",
    "PE": "PE", "PER": "PE", "PERU": "PE",
    "VE": "VE", "VEN": "VE", "VENEZUELA": "VE",
    "CN": "CN", "CHN": "CN", "CHINA": "CN",
    "JP": "JP", "JPN": "JP", "JAPAN": "JP",
    "KR": "KR", "KOR": "KR", "SOUTHKOREA": "KR", "SUEDKOREA": "KR", "SÜDKOREA": "KR",
    "IN": "IN", "IND": "IN", "INDIA": "IN", "INDIEN": "IN",
    "AU": "AU", "AUS": "AU", "AUSTRALIA": "AU", "AUSTRALIEN": "AU",
    "NZ": "NZ", "NZL": "NZ", "NEWZEALAND": "NZ", "NEUSEELAND": "NZ",
    "ZA": "ZA", "ZAF": "ZA", "SOUTHAFRICA": "ZA", "SUEDAFRIKA": "ZA", "SÜDAFRIKA": "ZA",
    "EG": "EG", "EGY": "EG", "EGYPT": "EG", "AEGYPTEN": "EG", "ÄGYPTEN": "EG",
    "NG": "NG", "NGA": "NG", "NIGERIA": "NG",
    "KE": "KE", "KEN": "KE", "KENYA": "KE", "KENIA": "KE",
    "MA": "MA", "MAR": "MA", "MOROCCO": "MA", "MAROKKO": "MA",
    "IL": "IL", "ISR": "IL", "ISRAEL": "IL",
    "SA": "SA", "SAU": "SA", "SAUDIARABIA": "SA", "SAUDIARABIEN": "SA",
    "AE": "AE", "ARE": "AE", "UNITEDARABEMIRATES": "AE", "VEREINIGTEARABISCHEEMIRATE": "AE",
    "TH": "TH", "THA": "TH", "THAILAND": "TH",
    "VN": "VN", "VNM": "VN", "VIETNAM": "VN",
    "ID": "ID", "IDN": "ID", "INDONESIA": "ID", "INDONESIEN": "ID",
    "MY": "MY", "MYS": "MY", "MALAYSIA": "MY",
    "SG": "SG", "SGP": "SG", "SINGAPORE": "SG", "SINGAPUR": "SG",
    "PH": "PH", "PHL": "PH", "PHILIPPINES": "PH", "PHILIPPINEN": "PH",
    "PK": "PK", "PAK": "PK", "PAKISTAN": "PK",
    "BD": "BD", "BGD": "BD", "BANGLADESH": "BD",
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

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)