import os
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r4/cleaning_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r4/cleaning_hard/output.parquet"

country_map = {
    "DE": "DE", "DEU": "DE", "GER": "DE", "DEUTSCHLAND": "DE", "GERMANY": "DE",
    "US": "US", "USA": "US", "UNITED STATES": "US", "UNITED STATES OF AMERICA": "US", "VEREINIGTE STAATEN": "US", "VEREINIGTE STAATEN VON AMERIKA": "US",
    "GB": "GB", "GBR": "GB", "UK": "GB", "UNITED KINGDOM": "GB", "GREAT BRITAIN": "GB", "VEREINIGTES KÖNIGREICH": "GB", "VEREINIGTES KOENIGREICH": "GB", "GROSSBRITANNIEN": "GB",
    "FR": "FR", "FRA": "FR", "FRANCE": "FR", "FRANKREICH": "FR",
    "IT": "IT", "ITA": "IT", "ITALY": "IT", "ITALIEN": "IT",
    "ES": "ES", "ESP": "ES", "SPAIN": "ES", "SPANIEN": "ES",
    "AT": "AT", "AUT": "AT", "AUSTRIA": "AT", "ÖSTERREICH": "AT", "OESTERREICH": "AT",
    "CH": "CH", "CHE": "CH", "SWITZERLAND": "CH", "SCHWEIZ": "CH",
    "NL": "NL", "NLD": "NL", "NETHERLANDS": "NL", "NIEDERLANDE": "NL", "HOLLAND": "NL", "THE NETHERLANDS": "NL",
    "BE": "BE", "BEL": "BE", "BELGIUM": "BE", "BELGIEN": "BE",
    "PL": "PL", "POL": "PL", "POLAND": "PL", "POLEN": "PL",
    "CA": "CA", "CAN": "CA", "CANADA": "CA", "KANADA": "CA",
    "AU": "AU", "AUS": "AU", "AUSTRALIA": "AU", "AUSTRALIEN": "AU",
    "BR": "BR", "BRA": "BR", "BRAZIL": "BR", "BRASILIEN": "BR",
    "IN": "IN", "IND": "IN", "INDIA": "IN", "INDIEN": "IN",
    "CN": "CN", "CHN": "CN", "CHINA": "CN",
    "JP": "JP", "JPN": "JP", "JAPAN": "JP",
    "RU": "RU", "RUS": "RU", "RUSSIA": "RU", "RUSSLAND": "RU",
    "SE": "SE", "SWE": "SE", "SWEDEN": "SE", "SCHWEDEN": "SE",
    "NO": "NO", "NOR": "NO", "NORWAY": "NO", "NORWEGEN": "NO",
    "DK": "DK", "DNK": "DK", "DENMARK": "DK", "DÄNEMARK": "DK", "DAENEMARK": "DK",
    "FI": "FI", "FIN": "FI", "FINLAND": "FI", "FINNLAND": "FI",
    "PT": "PT", "PRT": "PT", "PORTUGAL": "PT",
    "GR": "GR", "GRC": "GR", "GREECE": "GR", "GRIECHENLAND": "GR",
    "IE": "IE", "IRL": "IE", "IRELAND": "IE", "IRLAND": "IE",
    "TR": "TR", "TUR": "TR", "TURKEY": "TR", "TÜRKEI": "TR", "TUERKEI": "TR",
    "MX": "MX", "MEX": "MX", "MEXICO": "MX", "MEXIKO": "MX",
    "ZA": "ZA", "ZAF": "ZA", "SOUTH AFRICA": "ZA", "SÜDAFRIKA": "ZA", "SUEDAFRIKA": "ZA",
    "NZ": "NZ", "NZL": "NZ", "NEW ZEALAND": "NZ", "NEUSEELAND": "NZ",
    "CZ": "CZ", "CZE": "CZ", "CZECHIA": "CZ", "CZECH REPUBLIC": "CZ", "TSCHECHIEN": "CZ",
    "HU": "HU", "HUN": "HU", "HUNGARY": "HU", "UNGARN": "HU",
    "RO": "RO", "ROU": "RO", "ROMANIA": "RO", "RUMÄNIEN": "RO", "RUMAENIEN": "RO",
    "UA": "UA", "UKR": "UA", "UKRAINE": "UA",
    "LU": "LU", "LUX": "LU", "LUXEMBOURG": "LU", "LUXEMBURG": "LU",
    "LI": "LI", "LIE": "LI", "LIECHTENSTEIN": "LI",
    "HR": "HR", "HRV": "HR", "CROATIA": "HR", "KROATIEN": "HR",
    "SI": "SI", "SVN": "SI", "SLOVENIA": "SI", "SLOWENIEN": "SI",
    "SK": "SK", "SVK": "SK", "SLOVAKIA": "SK", "SLOWAKEI": "SK",
    "BG": "BG", "BGR": "BG", "BULGARIA": "BG", "BULGARIEN": "BG",
    "AR": "AR", "ARG": "AR", "ARGENTINA": "AR", "ARGENTINIEN": "AR",
    "EG": "EG", "EGY": "EG", "EGYPT": "EG", "ÄGYPTEN": "EG", "AEGYPTEN": "EG",
    "IL": "IL", "ISR": "IL", "ISRAEL": "IL",
    "KR": "KR", "KOR": "KR", "SOUTH KOREA": "KR", "SÜDKOREA": "KR", "SUEDKOREA": "KR",
    "SG": "SG", "SGP": "SG", "SINGAPORE": "SG", "SINGAPUR": "SG",
    "TH": "TH", "THA": "TH", "THAILAND": "TH"
}

def normalize_country(val):
    if pd.isna(val) or val is None:
        return "UNKNOWN"
    s = str(val).strip().upper()
    if not s or s in ("NAN", "NONE", "NULL", "UNKNOWN", "NA"):
        return "UNKNOWN"
    s_nodots = s.replace(".", "")
    if s_nodots in country_map:
        return country_map[s_nodots]
    if s in country_map:
        return country_map[s]
    return "UNKNOWN"

df = pd.read_parquet(input_path)
df['country'] = df['country'].apply(normalize_country)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)