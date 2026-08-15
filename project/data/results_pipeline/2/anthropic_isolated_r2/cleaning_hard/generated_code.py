import pandas as pd
import numpy as np

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_medium/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_isolated_r2/cleaning_hard/output.parquet"

df = pd.read_parquet(input_path)

country_map = {
    "DE": "DE", "DEU": "DE", "GERMANY": "DE", "DEUTSCHLAND": "DE", "GER": "DE", "ALLEMAGNE": "DE",
    "AT": "AT", "AUT": "AT", "AUSTRIA": "AT", "OESTERREICH": "AT", "ÖSTERREICH": "AT",
    "CH": "CH", "CHE": "CH", "SWITZERLAND": "CH", "SCHWEIZ": "CH", "SUISSE": "CH", "SVIZZERA": "CH",
    "US": "US", "USA": "US", "UNITEDSTATES": "US", "UNITEDSTATESOFAMERICA": "US", "VEREINIGTESTAATEN": "US", "VEREINIGTESTAATENVONAMERIKA": "US",
    "UK": "GB", "GB": "GB", "GBR": "GB", "UNITEDKINGDOM": "GB", "GROSSBRITANNIEN": "GB", "GROßBRITANNIEN": "GB", "VEREINIGTESKOENIGREICH": "GB", "VEREINIGTESKÖNIGREICH": "GB", "ENGLAND": "GB",
    "FR": "FR", "FRA": "FR", "FRANCE": "FR", "FRANKREICH": "FR",
    "ES": "ES", "ESP": "ES", "SPAIN": "ES", "SPANIEN": "ES",
    "IT": "IT", "ITA": "IT", "ITALY": "IT", "ITALIEN": "IT", "ITALIA": "IT",
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
    "RU": "RU", "RUS": "RU", "RUSSIA": "RU", "RUSSLAND": "RU",
    "UA": "UA", "UKR": "UA", "UKRAINE": "UA",
    "TR": "TR", "TUR": "TR", "TURKEY": "TR", "TUERKEI": "TR", "TÜRKEI": "TR",
    "CN": "CN", "CHN": "CN", "CHINA": "CN",
    "JP": "JP", "JPN": "JP", "JAPAN": "JP",
    "KR": "KR", "KOR": "KR", "SOUTHKOREA": "KR", "SUEDKOREA": "KR", "SÜDKOREA": "KR",
    "IN": "IN", "IND": "IN", "INDIA": "IN", "INDIEN": "IN",
    "AU": "AU", "AUS": "AU", "AUSTRALIA": "AU", "AUSTRALIEN": "AU",
    "CA": "CA", "CAN": "CA", "CANADA": "CA", "KANADA": "CA",
    "MX": "MX", "MEX": "MX", "MEXICO": "MX", "MEXIKO": "MX",
    "BR": "BR", "BRA": "BR", "BRAZIL": "BR", "BRASILIEN": "BR",
    "AR": "AR", "ARG": "AR", "ARGENTINA": "AR", "ARGENTINIEN": "AR",
    "ZA": "ZA", "ZAF": "ZA", "SOUTHAFRICA": "ZA", "SUEDAFRIKA": "ZA", "SÜDAFRIKA": "ZA",
    "EG": "EG", "EGY": "EG", "EGYPT": "EG", "AEGYPTEN": "EG", "ÄGYPTEN": "EG",
    "IL": "IL", "ISR": "IL", "ISRAEL": "IL",
    "SA": "SA", "SAU": "SA", "SAUDIARABIA": "SA", "SAUDIARABIEN": "SA",
    "AE": "AE", "ARE": "AE", "UNITEDARABEMIRATES": "AE", "VEREINIGTEARABISCHEEMIRATE": "AE",
    "SG": "SG", "SGP": "SG", "SINGAPORE": "SG", "SINGAPUR": "SG",
    "MY": "MY", "MYS": "MY", "MALAYSIA": "MY",
    "TH": "TH", "THA": "TH", "THAILAND": "TH",
    "ID": "ID", "IDN": "ID", "INDONESIA": "ID", "INDONESIEN": "ID",
    "PH": "PH", "PHL": "PH", "PHILIPPINES": "PH", "PHILIPPINEN": "PH",
    "VN": "VN", "VNM": "VN", "VIETNAM": "VN",
    "NZ": "NZ", "NZL": "NZ", "NEWZEALAND": "NZ", "NEUSEELAND": "NZ",
    "LU": "LU", "LUX": "LU", "LUXEMBOURG": "LU", "LUXEMBURG": "LU",
    "IS": "IS", "ISL": "IS", "ICELAND": "IS", "ISLAND": "IS",
    "EE": "EE", "EST": "EE", "ESTONIA": "EE", "ESTLAND": "EE",
    "LV": "LV", "LVA": "LV", "LATVIA": "LV", "LETTLAND": "LV",
    "LT": "LT", "LTU": "LT", "LITHUANIA": "LT", "LITAUEN": "LT",
    "CY": "CY", "CYP": "CY", "CYPRUS": "CY", "ZYPERN": "CY",
    "MT": "MT", "MLT": "MT", "MALTA": "MT",
    "CL": "CL", "CHL": "CL", "CHILE": "CL",
    "CO": "CO", "COL": "CO", "COLOMBIA": "CO", "KOLUMBIEN": "CO",
    "PE": "PE", "PER": "PE", "PERU": "PE",
    "VE": "VE", "VEN": "VE", "VENEZUELA": "VE",
}

def normalize_key(s):
    if pd.isna(s):
        return None
    s = str(s).strip().upper()
    s = s.replace(".", "").replace("-", "").replace("_", "").replace(" ", "")
    return s

def map_country(val):
    key = normalize_key(val)
    if key is None or key == "":
        return "UNKNOWN"
    return country_map.get(key, "UNKNOWN")

df["country"] = df["country"].apply(map_country)

df.to_parquet(output_path, index=False)