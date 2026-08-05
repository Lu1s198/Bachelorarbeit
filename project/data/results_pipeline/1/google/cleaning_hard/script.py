import os
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/cleaning_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/cleaning_hard/output.parquet"

df = pd.read_parquet(input_path)

country_map = {
    # DE
    "DE": "DE",
    "DEU": "DE",
    "GER": "DE",
    "GERMANY": "DE",
    "DEUTSCHLAND": "DE",
    "BRD": "DE",
    # US
    "US": "US",
    "USA": "US",
    "UNITED STATES": "US",
    "UNITED STATES OF AMERICA": "US",
    "VEREINIGTE STAATEN": "US",
    "VEREINIGTE STAATEN VON AMERIKA": "US",
    # GB
    "GB": "GB",
    "GBR": "GB",
    "UK": "GB",
    "UNITED KINGDOM": "GB",
    "GREAT BRITAIN": "GB",
    "GROSSBRITANNIEN": "GB",
    "GROSSBRITANNIEN (VEREINIGTES KÖNIGREICH)": "GB",
    "VEREINIGTES KÖNIGREICH": "GB",
    "VEREINIGTES KOENIGREICH": "GB",
    "ENGLAND": "GB",
    "SCOTLAND": "GB",
    "WALES": "GB",
    # FR
    "FR": "FR",
    "FRA": "FR",
    "FRANCE": "FR",
    "FRANKREICH": "FR",
    # IT
    "IT": "IT",
    "ITA": "IT",
    "ITALY": "IT",
    "ITALIEN": "IT",
    # ES
    "ES": "ES",
    "ESP": "ES",
    "SPAIN": "ES",
    "SPANIEN": "ES",
    # AT
    "AT": "AT",
    "AUT": "AT",
    "AUSTRIA": "AT",
    "ÖSTERREICH": "AT",
    "OESTERREICH": "AT",
    # CH
    "CH": "CH",
    "CHE": "CH",
    "SUI": "CH",
    "SWITZERLAND": "CH",
    "SCHWEIZ": "CH",
    # NL
    "NL": "NL",
    "NLD": "NL",
    "NED": "NL",
    "NETHERLANDS": "NL",
    "NIEDERLANDE": "NL",
    "HOLLAND": "NL",
    "THE NETHERLANDS": "NL",
    # BE
    "BE": "BE",
    "BEL": "BE",
    "BELGIUM": "BE",
    "BELGIEN": "BE",
    # PL
    "PL": "PL",
    "POL": "PL",
    "POLAND": "PL",
    "POLEN": "PL",
    # CZ
    "CZ": "CZ",
    "CZE": "CZ",
    "CZECH REPUBLIC": "CZ",
    "CZECHIA": "CZ",
    "TSCHECHIEN": "CZ",
    "TSCHECHISCHE REPUBLIK": "CZ",
    # DK
    "DK": "DK",
    "DNK": "DK",
    "DENMARK": "DK",
    "DÄNEMARK": "DK",
    "DAENEMARK": "DK",
    # SE
    "SE": "SE",
    "SWE": "SE",
    "SWEDEN": "SE",
    "SCHWEDEN": "SE",
    # NO
    "NO": "NO",
    "NOR": "NO",
    "NORWAY": "NO",
    "NORWEGEN": "NO",
    # FI
    "FI": "FI",
    "FIN": "FI",
    "FINLAND": "FI",
    "FINNLAND": "FI",
    # PT
    "PT": "PT",
    "PRT": "PT",
    "PORTUGAL": "PT",
    # IE
    "IE": "IE",
    "IRL": "IE",
    "IRELAND": "IE",
    "IRLAND": "IE",
    # GR
    "GR": "GR",
    "GRC": "GR",
    "GRE": "GR",
    "GREECE": "GR",
    "GRIECHENLAND": "GR",
    # RU
    "RU": "RU",
    "RUS": "RU",
    "RUSSIA": "RU",
    "RUSSLAND": "RU",
    "RUSSIAN FEDERATION": "RU",
    # CN
    "CN": "CN",
    "CHN": "CN",
    "CHINA": "CN",
    "PEOPLES REPUBLIC OF CHINA": "CN",
    "VOLKSREPUBLIK CHINA": "CN",
    # JP
    "JP": "JP",
    "JPN": "JP",
    "JAPAN": "JP",
    # IN
    "IN": "IN",
    "IND": "IN",
    "INDIA": "IN",
    "INDIEN": "IN",
    # BR
    "BR": "BR",
    "BRA": "BR",
    "BRAZIL": "BR",
    "BRASILIEN": "BR",
    # CA
    "CA": "CA",
    "CAN": "CA",
    "CANADA": "CA",
    "KANADA": "CA",
    # AU
    "AU": "AU",
    "AUS": "AU",
    "AUSTRALIA": "AU",
    "AUSTRALIEN": "AU",
    # MX
    "MX": "MX",
    "MEX": "MX",
    "MEXICO": "MX",
    "MEXIKO": "MX",
    # ZA
    "ZA": "ZA",
    "ZAF": "ZA",
    "RSA": "ZA",
    "SOUTH AFRICA": "ZA",
    "SÜDAFRIKA": "ZA",
    "SUEDAFRIKA": "ZA",
    # TR
    "TR": "TR",
    "TUR": "TR",
    "TURKEY": "TR",
    "TÜRKEI": "TR",
    "TUERKEI": "TR",
    "TÜRKIYE": "TR",
    # HU
    "HU": "HU",
    "HUN": "HU",
    "HUNGARY": "HU",
    "UNGARN": "HU",
    # RO
    "RO": "RO",
    "ROU": "RO",
    "ROMANIA": "RO",
    "RUMÄNIEN": "RO",
    "RUMAENIEN": "RO",
    # BG
    "BG": "BG",
    "BGR": "BG",
    "BULGARIA": "BG",
    "BULGARIEN": "BG",
    # HR
    "HR": "HR",
    "HRV": "HR",
    "CROATIA": "HR",
    "KROATIEN": "HR",
    # SK
    "SK": "SK",
    "SVK": "SK",
    "SLOVAKIA": "SK",
    "SLOWAKEI": "SK",
    # SI
    "SI": "SI",
    "SVN": "SI",
    "SLOVENIA": "SI",
    "SLOWENIEN": "SI",
    # EE
    "EE": "EE",
    "EST": "EE",
    "ESTONIA": "EE",
    "ESTLAND": "EE",
    # LV
    "LV": "LV",
    "LVA": "LV",
    "LATVIA": "LV",
    "LETTLAND": "LV",
    # LT
    "LT": "LT",
    "LTU": "LT",
    "LITHUANIA": "LT",
    "LITAUEN": "LT",
    # LU
    "LU": "LU",
    "LUX": "LU",
    "LUXEMBOURG": "LU",
    "LUXEMBURG": "LU",
    # MT
    "MT": "MT",
    "MLT": "MT",
    "MALTA": "MT",
    # CY
    "CY": "CY",
    "CYP": "CY",
    "CYPRUS": "CY",
    "ZYPERN": "CY",
    # IS
    "IS": "IS",
    "ISL": "IS",
    "ICELAND": "IS",
    "ISLAND": "IS",
    # UA
    "UA": "UA",
    "UKR": "UA",
    "UKRAINE": "UA",
    # NZ
    "NZ": "NZ",
    "NZL": "NZ",
    "NEW ZEALAND": "NZ",
    "NEUSEELAND": "NZ",
    # KR
    "KR": "KR",
    "KOR": "KR",
    "SOUTH KOREA": "KR",
    "SÜDKOREA": "KR",
    "SUEDAFRIKA": "ZA",
    "SUEDKOREA": "KR",
    "KOREA": "KR",
    # SG
    "SG": "SG",
    "SGP": "SG",
    "SINGAPORE": "SG",
    "SINGAPUR": "SG",
    # AE
    "AE": "AE",
    "ARE": "AE",
    "UAE": "AE",
    "UNITED ARAB EMIRATES": "AE",
    "VEREINIGTE ARABISCHE EMIRATE": "AE",
    # IL
    "IL": "IL",
    "ISR": "IL",
    "ISRAEL": "IL",
    # EG
    "EG": "EG",
    "EGY": "EG",
    "EGYPT": "EG",
    "ÄGYPTEN": "EG",
    "AEGYPTEN": "EG",
    # TH
    "TH": "TH",
    "THA": "TH",
    "THAILAND": "TH",
    # VN
    "VN": "VN",
    "VNM": "VN",
    "VIETNAM": "VN",
    # ID
    "ID": "ID",
    "IDN": "ID",
    "INDONESIA": "ID",
    "INDONESIEN": "ID",
    # MY
    "MY": "MY",
    "MYS": "MY",
    "MALAYSIA": "MY",
    # PH
    "PH": "PH",
    "PHL": "PH",
    "PHILIPPINES": "PH",
    "PHILIPPINEN": "PH",
    # AR
    "AR": "AR",
    "ARG": "AR",
    "ARGENTINA": "AR",
    "ARGENTINIEN": "AR",
    # CL
    "CL": "CL",
    "CHL": "CL",
    "CHILE": "CL",
    # CO
    "CO": "CO",
    "COL": "CO",
    "COLOMBIA": "CO",
    "KOLUMBIEN": "CO",
    # PE
    "PE": "PE",
    "PER": "PE",
    "PERU": "PE",
    # LI
    "LI": "LI",
    "LIE": "LI",
    "LIECHTENSTEIN": "LI",
    # MC
    "MC": "MC",
    "MCO": "MC",
    "MONACO": "MC",
}

cleaned_country = (
    df["country"]
    .astype(str)
    .str.strip()
    .str.upper()
    .str.replace(r"\.", "", regex=True)
)

df["country"] = cleaned_country.map(country_map).fillna("UNKNOWN")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)