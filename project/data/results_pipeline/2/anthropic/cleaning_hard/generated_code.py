import pandas as pd
import numpy as np

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic/cleaning_medium/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic/cleaning_hard/output.parquet"

df = pd.read_parquet(input_path)

country_map = {
    "DE": "DE", "DEU": "DE", "GER": "DE", "GERMANY": "DE", "DEUTSCHLAND": "DE",
    "AT": "AT", "AUT": "AT", "AUSTRIA": "AT", "OESTERREICH": "AT", "ÖSTERREICH": "AT",
    "CH": "CH", "CHE": "CH", "SWITZERLAND": "CH", "SCHWEIZ": "CH",
    "US": "US", "USA": "US", "UNITEDSTATES": "US", "UNITEDSTATESOFAMERICA": "US", "VEREINIGTESTAATEN": "US",
    "GB": "GB", "UK": "GB", "GBR": "GB", "UNITEDKINGDOM": "GB", "GREATBRITAIN": "GB", "GROSSBRITANNIEN": "GB", "VEREINIGTESKOENIGREICH": "GB",
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
    "NZ": "NZ", "NZL": "NZL" if False else "NZ", "NEWZEALAND": "NZ", "NEUSEELAND": "NZ",
    "CA": "CA", "CAN": "CA", "CANADA": "CA", "KANADA": "CA",
    "MX": "MX", "MEX": "MX", "MEXICO": "MX", "MEXIKO": "MX",
    "BR": "BR", "BRA": "BR", "BRAZIL": "BR", "BRASILIEN": "BR",
    "AR": "AR", "ARG": "AR", "ARGENTINA": "AR", "ARGENTINIEN": "AR",
    "ZA": "ZA", "ZAF": "ZA", "SOUTHAFRICA": "ZA", "SUEDAFRIKA": "ZA", "SÜDAFRIKA": "ZA",
    "EG": "EG", "EGY": "EG", "EGYPT": "EG", "AEGYPTEN": "EG", "ÄGYPTEN": "EG",
    "IL": "IL", "ISR": "IL", "ISRAEL": "IL",
    "SA": "SA", "SAU": "SA", "SAUDIARABIA": "SA", "SAUDIARABIEN": "SA",
    "AE": "AE", "ARE": "AE", "UAE": "AE", "UNITEDARABEMIRATES": "AE", "VEREINIGTEARABISCHEEMIRATE": "AE",
    "TH": "TH", "THA": "TH", "THAILAND": "TH",
    "VN": "VN", "VNM": "VN", "VIETNAM": "VN",
    "ID": "ID", "IDN": "ID", "INDONESIA": "ID", "INDONESIEN": "ID",
    "MY": "MY", "MYS": "MY", "MALAYSIA": "MY",
    "SG": "SG", "SGP": "SG", "SINGAPORE": "SG", "SINGAPUR": "SG",
    "PH": "PH", "PHL": "PH", "PHILIPPINES": "PH", "PHILIPPINEN": "PH",
    "PK": "PK", "PAK": "PK", "PAKISTAN": "PK",
    "BD": "BD", "BGD": "BD", "BANGLADESH": "BD",
    "NG": "NG", "NGA": "NG", "NIGERIA": "NG",
    "KE": "KE", "KEN": "KE", "KENYA": "KE", "KENIA": "KE",
    "MA": "MA", "MAR": "MA", "MOROCCO": "MA", "MAROKKO": "MA",
    "DZ": "DZ", "DZA": "DZ", "ALGERIA": "DZ", "ALGERIEN": "DZ",
    "TN": "TN", "TUN": "TN", "TUNISIA": "TN", "TUNESIEN": "TN",
    "CL": "CL", "CHL": "CL", "CHILE": "CL",
    "CO": "CO", "COL": "CO", "COLOMBIA": "CO", "KOLUMBIEN": "CO",
    "PE": "PE", "PER": "PE", "PERU": "PE",
    "VE": "VE", "VEN": "VE", "VENEZUELA": "VE",
    "CU": "CU", "CUB": "CU", "CUBA": "CU", "KUBA": "CU",
    "IS": "IS", "ISL": "IS", "ICELAND": "IS", "ISLAND": "IS",
    "EE": "EE", "EST": "EE", "ESTONIA": "EE", "ESTLAND": "EE",
    "LV": "LV", "LVA": "LV", "LATVIA": "LV", "LETTLAND": "LV",
    "LT": "LT", "LTU": "LT", "LITHUANIA": "LT", "LITAUEN": "LT",
    "MT": "MT", "MLT": "MT", "MALTA": "MT",
    "CY": "CY", "CYP": "CY", "CYPRUS": "CY", "ZYPERN": "CY",
    "AL": "AL", "ALB": "AL", "ALBANIA": "AL", "ALBANIEN": "AL",
    "BA": "BA", "BIH": "BA", "BOSNIA": "BA", "BOSNIEN": "BA",
    "MK": "MK", "MKD": "MK", "MACEDONIA": "MK", "MAZEDONIEN": "MK",
    "ME": "ME", "MNE": "ME", "MONTENEGRO": "ME",
    "MD": "MD", "MDA": "MD", "MOLDOVA": "MD", "MOLDAWIEN": "MD",
    "BY": "BY", "BLR": "BY", "BELARUS": "BY", "WEISSRUSSLAND": "BY",
    "LI": "LI", "LIE": "LI", "LIECHTENSTEIN": "LI",
    "MC": "MC", "MCO": "MC", "MONACO": "MC",
    "AD": "AD", "AND": "AD", "ANDORRA": "AD",
    "SM": "SM", "SMR": "SM", "SANMARINO": "SM",
    "VA": "VA", "VAT": "VA", "VATICAN": "VA", "VATIKAN": "VA",
}

def normalize_country(value):
    if pd.isna(value):
        return "UNKNOWN"
    s = str(value).strip().upper()
    s = s.replace(".", "").replace("-", "").replace("_", "").replace(" ", "")
    s = s.replace("Ä", "AE").replace("Ö", "OE").replace("Ü", "UE").replace("ß", "SS")
    if s in country_map:
        return country_map[s]
    # try without umlaut replacement fallback (already applied)
    return "UNKNOWN"

df["country"] = df["country"].apply(normalize_country)

df.to_parquet(output_path, index=False)