import pandas as pd
import numpy as np

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/_reference/cleaning_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/anthropic_isolated/cleaning_hard/output.parquet"

df = pd.read_parquet(input_path)

country_map = {
    "DE": "DE", "DEU": "DE", "GERMANY": "DE", "GERMAN": "DE", "DEUTSCHLAND": "DE", "ALLEMAGNE": "DE",
    "AT": "AT", "AUT": "AT", "AUSTRIA": "AT", "OESTERREICH": "AT", "ÖSTERREICH": "AT",
    "CH": "CH", "CHE": "CH", "SWITZERLAND": "CH", "SCHWEIZ": "CH", "SUISSE": "CH",
    "US": "US", "USA": "US", "UNITEDSTATES": "US", "UNITEDSTATESOFAMERICA": "US", "VEREINIGTESTAATEN": "US", "AMERICA": "US",
    "GB": "GB", "UK": "GB", "GBR": "GB", "UNITEDKINGDOM": "GB", "GREATBRITAIN": "GB", "GROSSBRITANNIEN": "GB", "VEREINIGTESKONIGREICH": "GB", "ENGLAND": "GB",
    "FR": "FR", "FRA": "FR", "FRANCE": "FR", "FRANKREICH": "FR",
    "IT": "IT", "ITA": "IT", "ITALY": "IT", "ITALIEN": "IT", "ITALIA": "IT",
    "ES": "ES", "ESP": "ES", "SPAIN": "ES", "SPANIEN": "ES", "ESPANA": "ES",
    "PT": "PT", "PRT": "PT", "PORTUGAL": "PT",
    "NL": "NL", "NLD": "NL", "NETHERLANDS": "NL", "NIEDERLANDE": "NL", "HOLLAND": "NL",
    "BE": "BE", "BEL": "BE", "BELGIUM": "BE", "BELGIEN": "BE",
    "LU": "LU", "LUX": "LU", "LUXEMBOURG": "LU", "LUXEMBURG": "LU",
    "PL": "PL", "POL": "PL", "POLAND": "PL", "POLEN": "PL",
    "CZ": "CZ", "CZE": "CZ", "CZECHREPUBLIC": "CZ", "TSCHECHIEN": "CZ", "CZECHIA": "CZ",
    "SK": "SK", "SVK": "SK", "SLOVAKIA": "SK", "SLOWAKEI": "SK",
    "HU": "HU", "HUN": "HU", "HUNGARY": "HU", "UNGARN": "HU",
    "RO": "RO", "ROU": "RO", "ROMANIA": "RO", "RUMANIEN": "RO",
    "BG": "BG", "BGR": "BG", "BULGARIA": "BG", "BULGARIEN": "BG",
    "GR": "GR", "GRC": "GR", "GREECE": "GR", "GRIECHENLAND": "GR",
    "SE": "SE", "SWE": "SE", "SWEDEN": "SE", "SCHWEDEN": "SE",
    "NO": "NO", "NOR": "NO", "NORWAY": "NO", "NORWEGEN": "NO",
    "DK": "DK", "DNK": "DK", "DENMARK": "DK", "DANEMARK": "DK",
    "FI": "FI", "FIN": "FI", "FINLAND": "FI", "FINNLAND": "FI",
    "IE": "IE", "IRL": "IE", "IRELAND": "IE", "IRLAND": "IE",
    "IS": "IS", "ISL": "IS", "ICELAND": "IS", "ISLAND": "IS",
    "RU": "RU", "RUS": "RU", "RUSSIA": "RU", "RUSSLAND": "RU",
    "UA": "UA", "UKR": "UA", "UKRAINE": "UA",
    "TR": "TR", "TUR": "TR", "TURKEY": "TR", "TUERKEI": "TR", "TÜRKEI": "TR",
    "CN": "CN", "CHN": "CN", "CHINA": "CN",
    "JP": "JP", "JPN": "JP", "JAPAN": "JP",
    "KR": "KR", "KOR": "KR", "SOUTHKOREA": "KR", "SUEDKOREA": "KR", "SÜDKOREA": "KR",
    "IN": "IN", "IND": "IN", "INDIA": "IN", "INDIEN": "IN",
    "AU": "AU", "AUS": "AU", "AUSTRALIA": "AU", "AUSTRALIEN": "AU",
    "NZ": "NZ", "NZL": "NZ", "NEWZEALAND": "NZ", "NEUSEELAND": "NZ",
    "CA": "CA", "CAN": "CA", "CANADA": "CA", "KANADA": "CA",
    "MX": "MX", "MEX": "MX", "MEXICO": "MX", "MEXIKO": "MX",
    "BR": "BR", "BRA": "BR", "BRAZIL": "BR", "BRASILIEN": "BR",
    "AR": "AR", "ARG": "AR", "ARGENTINA": "AR", "ARGENTINIEN": "AR",
    "CL": "CL", "CHL": "CL", "CHILE": "CL",
    "ZA": "ZA", "ZAF": "ZA", "SOUTHAFRICA": "ZA", "SUEDAFRIKA": "ZA", "SÜDAFRIKA": "ZA",
    "EG": "EG", "EGY": "EG", "EGYPT": "EG", "AEGYPTEN": "EG", "ÄGYPTEN": "EG",
    "IL": "IL", "ISR": "IL", "ISRAEL": "IL",
    "SA": "SA", "SAU": "SA", "SAUDIARABIA": "SA", "SAUDIARABIEN": "SA",
    "AE": "AE", "ARE": "AE", "UNITEDARABEMIRATES": "AE", "VEREINIGTEARABISCHEEMIRATE": "AE",
    "SG": "SG", "SGP": "SG", "SINGAPORE": "SG", "SINGAPUR": "SG",
    "MY": "MY", "MYS": "MY", "MALAYSIA": "MY",
    "TH": "TH", "THA": "TH", "THAILAND": "TH",
    "ID": "ID", "IDN": "ID", "INDONESIA": "ID", "INDONESIEN": "ID",
    "VN": "VN", "VNM": "VN", "VIETNAM": "VN",
    "PH": "PH", "PHL": "PH", "PHILIPPINES": "PH", "PHILIPPINEN": "PH",
    "PK": "PK", "PAK": "PK", "PAKISTAN": "PK",
    "BD": "BD", "BGD": "BD", "BANGLADESH": "BD",
    "HR": "HR", "HRV": "HR", "CROATIA": "HR", "KROATIEN": "HR",
    "SI": "SI", "SVN": "SI", "SLOVENIA": "SI", "SLOWENIEN": "SI",
    "RS": "RS", "SRB": "RS", "SERBIA": "RS", "SERBIEN": "RS",
    "BA": "BA", "BIH": "BA", "BOSNIA": "BA", "BOSNIEN": "BA",
    "AL": "AL", "ALB": "AL", "ALBANIA": "AL", "ALBANIEN": "AL",
    "LT": "LT", "LTU": "LT", "LITHUANIA": "LT", "LITAUEN": "LT",
    "LV": "LV", "LVA": "LV", "LATVIA": "LV", "LETTLAND": "LV",
    "EE": "EE", "EST": "EE", "ESTONIA": "EE", "ESTLAND": "EE",
    "CY": "CY", "CYP": "CY", "CYPRUS": "CY", "ZYPERN": "CY",
    "MT": "MT", "MLT": "MT", "MALTA": "MT",
    "IS_": "IS",
    "LI": "LI", "LIE": "LI", "LIECHTENSTEIN": "LI",
    "MC": "MC", "MCO": "MC", "MONACO": "MC",
    "AD": "AD", "AND": "AD", "ANDORRA": "AD",
    "SM": "SM", "SMR": "SM", "SANMARINO": "SM",
    "VA": "VA", "VAT": "VA", "VATICAN": "VA",
    "BY": "BY", "BLR": "BY", "BELARUS": "BY", "WEISSRUSSLAND": "BY",
    "MD": "MD", "MDA": "MD", "MOLDOVA": "MD", "MOLDAWIEN": "MD",
    "GE": "GE", "GEO": "GE", "GEORGIA": "GE", "GEORGIEN": "GE",
    "AM": "AM", "ARM": "AM", "ARMENIA": "AM", "ARMENIEN": "AM",
    "AZ": "AZ", "AZE": "AZ", "AZERBAIJAN": "AZ", "ASERBAIDSCHAN": "AZ",
    "KZ": "KZ", "KAZ": "KZ", "KAZAKHSTAN": "KZ", "KASACHSTAN": "KZ",
    "NG": "NG", "NGA": "NG", "NIGERIA": "NG",
    "KE": "KE", "KEN": "KE", "KENYA": "KE", "KENIA": "KE",
    "MA": "MA", "MAR": "MA", "MOROCCO": "MA", "MAROKKO": "MA",
    "TN": "TN", "TUN": "TN", "TUNISIA": "TN", "TUNESIEN": "TN",
    "DZ": "DZ", "DZA": "DZ", "ALGERIA": "DZ", "ALGERIEN": "DZ",
    "CO": "CO", "COL": "CO", "COLOMBIA": "CO", "KOLUMBIEN": "CO",
    "PE": "PE", "PER": "PE", "PERU": "PE",
    "VE": "VE", "VEN": "VE", "VENEZUELA": "VE",
    "EC": "EC", "ECU": "EC", "ECUADOR": "EC",
    "UY": "UY", "URY": "UY", "URUGUAY": "UY",
    "PY": "PY", "PRY": "PY", "PARAGUAY": "PY",
    "BO": "BO", "BOL": "BO", "BOLIVIA": "BO", "BOLIVIEN": "BO",
    "CR": "CR", "CRI": "CR", "COSTARICA": "CR",
    "PA": "PA", "PAN": "PA", "PANAMA": "PA",
    "CU": "CU", "CUB": "CU", "CUBA": "CU", "KUBA": "CU",
    "DO": "DO", "DOM": "DO", "DOMINICANREPUBLIC": "DO", "DOMINIKANISCHEREPUBLIK": "DO",
    "JM": "JM", "JAM": "JM", "JAMAICA": "JM", "JAMAIKA": "JM",
    "IR": "IR", "IRN": "IR", "IRAN": "IR",
    "IQ": "IQ", "IRQ": "IQ", "IRAQ": "IQ", "IRAK": "IQ",
    "SY": "SY", "SYR": "SY", "SYRIA": "SY", "SYRIEN": "SY",
    "JO": "JO", "JOR": "JO", "JORDAN": "JO", "JORDANIEN": "JO",
    "LB": "LB", "LBN": "LB", "LEBANON": "LB", "LIBANON": "LB",
    "KW": "KW", "KWT": "KW", "KUWAIT": "KW",
    "QA": "QA", "QAT": "QA", "QATAR": "QA",
    "OM": "OM", "OMN": "OM", "OMAN": "OM",
    "BH": "BH", "BHR": "BH", "BAHRAIN": "BH",
    "AF": "AF", "AFG": "AF", "AFGHANISTAN": "AF",
    "LK": "LK", "LKA": "LK", "SRILANKA": "LK",
    "NP": "NP", "NPL": "NP", "NEPAL": "NP",
    "MM": "MM", "MMR": "MM", "MYANMAR": "MM",
    "KH": "KH", "KHM": "KH", "CAMBODIA": "KH", "KAMBODSCHA": "KH",
    "LA": "LA", "LAO": "LA", "LAOS": "LA",
    "MN": "MN", "MNG": "MN", "MONGOLIA": "MN", "MONGOLEI": "MN",
    "TW": "TW", "TWN": "TW", "TAIWAN": "TW",
    "HK": "HK", "HKG": "HK", "HONGKONG": "HK",
}

def normalize_key(s):
    if s is None:
        return ""
    s = str(s).strip().upper()
    s = s.replace(".", "").replace("-", "").replace("_", "").replace(" ", "")
    replacements = {
        "Ä": "AE", "Ö": "OE", "Ü": "UE", "ß": "SS"
    }
    for a, b in replacements.items():
        s = s.replace(a, b)
    return s

def map_country(val):
    key = normalize_key(val)
    if key in country_map:
        return country_map[key]
    # try alt with umlaut normalized differently already done
    return "UNKNOWN"

df["country"] = df["country"].apply(map_country)

df.to_parquet(output_path, index=False)