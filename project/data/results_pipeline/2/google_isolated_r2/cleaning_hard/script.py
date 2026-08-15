import os
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_medium/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_isolated_r2/cleaning_hard/output.parquet"

df = pd.read_parquet(input_path)

valid_iso_alpha2 = {
    "AD", "AE", "AF", "AG", "AI", "AL", "AM", "AO", "AQ", "AR", "AS", "AT", "AU", "AW", "AX", "AZ",
    "BA", "BB", "BD", "BE", "BF", "BG", "BH", "BI", "BJ", "BL", "BM", "BN", "BO", "BQ", "BR", "BS",
    "BT", "BV", "BW", "BY", "BZ", "CA", "CC", "CD", "CF", "CG", "CH", "CI", "CK", "CL", "CM", "CN",
    "CO", "CR", "CU", "CV", "CW", "CX", "CY", "CZ", "DE", "DJ", "DK", "DM", "DO", "DZ", "EC", "EE",
    "EG", "EH", "ER", "ES", "ET", "FI", "FJ", "FK", "FM", "FO", "FR", "GA", "GB", "GD", "GE", "GF",
    "GG", "GH", "GI", "GL", "GM", "GN", "GP", "GQ", "GR", "GS", "GT", "GU", "GW", "GY", "HK", "HM",
    "HN", "HR", "HT", "HU", "ID", "IE", "IL", "IM", "IN", "IO", "IQ", "IR", "IS", "IT", "JE", "JM",
    "JO", "JP", "KE", "KG", "KH", "KI", "KM", "KN", "KP", "KR", "KW", "KY", "KZ", "LA", "LB", "LC",
    "LI", "LK", "LR", "LS", "LT", "LU", "LV", "LY", "MA", "MC", "MD", "ME", "MF", "MG", "MH", "MK",
    "ML", "MM", "MN", "MO", "MP", "MQ", "MR", "MS", "MT", "MU", "MV", "MW", "MX", "MY", "MZ", "NA",
    "NC", "NE", "NF", "NG", "NI", "NL", "NO", "NP", "NR", "NU", "NZ", "OM", "PA", "PE", "PF", "PG",
    "PH", "PK", "PL", "PM", "PN", "PR", "PS", "PT", "PW", "PY", "QA", "RE", "RO", "RS", "RU", "RW",
    "SA", "SB", "SC", "SD", "SE", "SG", "SH", "SI", "SJ", "SK", "SL", "SM", "SN", "SO", "SR", "SS",
    "ST", "SV", "SX", "SY", "SZ", "TC", "TD", "TF", "TG", "TH", "TJ", "TK", "TL", "TM", "TN", "TO",
    "TR", "TT", "TV", "TW", "TZ", "UA", "UG", "UM", "US", "UY", "UZ", "VA", "VC", "VE", "VG", "VI",
    "VN", "VU", "WF", "WS", "YE", "YT", "ZA", "ZM", "ZW"
}

custom_map = {
    "deu": "DE", "ger": "DE", "deutschland": "DE", "germany": "DE", "brd": "DE", "bundesrepublik deutschland": "DE",
    "aut": "AT", "österreich": "AT", "oesterreich": "AT", "austria": "AT",
    "che": "CH", "sui": "CH", "schweiz": "CH", "switzerland": "CH", "suisse": "CH", "svizzera": "CH",
    "usa": "US", "united states": "US", "united states of america": "US", "vereinigte staaten": "US", "vereinigte staaten von amerika": "US", "vst": "US",
    "gbr": "GB", "uk": "GB", "united kingdom": "GB", "great britain": "GB", "großbritannien": "GB", "grossbritannien": "GB", "england": "GB",
    "fra": "FR", "france": "FR", "frankreich": "FR",
    "ita": "IT", "italy": "IT", "italien": "IT",
    "esp": "ES", "spain": "ES", "spanien": "ES",
    "nld": "NL", "netherlands": "NL", "niederlande": "NL", "holland": "NL",
    "pol": "PL", "poland": "PL", "polen": "PL",
    "bel": "BE", "belgium": "BE", "belgien": "BE",
    "can": "CA", "canada": "CA", "kanada": "CA",
    "chn": "CN", "china": "CN", "volksrepublik china": "CN",
    "jpn": "JP", "japan": "JP",
    "aus": "AU", "australia": "AU", "australien": "AU",
    "bra": "BR", "brazil": "BR", "brasilien": "BR",
    "rus": "RU", "russia": "RU", "russland": "RU", "russian federation": "RU",
    "ind": "IN", "india": "IN", "indien": "IN",
    "swe": "SE", "sweden": "SE", "schweden": "SE",
    "nor": "NO", "norway": "NO", "norwegen": "NO",
    "dnk": "DK", "denmark": "DK", "dänemark": "DK", "daenemark": "DK",
    "fin": "FI", "finland": "FI", "finnland": "FI",
    "prt": "PT", "portugal": "PT",
    "grc": "GR", "greece": "GR", "griechenland": "GR",
    "tur": "TR", "turkey": "TR", "türkei": "TR", "tuerkei": "TR",
    "irl": "IE", "ireland": "IE", "irland": "IE",
    "cze": "CZ", "czech republic": "CZ", "tschechien": "CZ", "czechia": "CZ", "tschechische republik": "CZ",
    "hun": "HU", "hungary": "HU", "ungarn": "HU",
    "mex": "MX", "mexico": "MX", "mexiko": "MX",
    "zaf": "ZA", "south africa": "ZA", "südafrika": "ZA", "suedafrika": "ZA",
    "kor": "KR", "south korea": "KR", "südkorea": "KR", "suedkorea": "KR", "korea": "KR",
    "arg": "AR", "argentina": "AR", "argentinien": "AR",
    "chl": "CL", "chile": "CL",
    "col": "CO", "colombia": "CO", "kolumbien": "CO",
    "nzl": "NZ", "new zealand": "NZ", "neuseeland": "NZ",
    "sgp": "SG", "singapore": "SG", "singapur": "SG",
    "are": "AE", "uae": "AE", "united arab emirates": "AE", "vereinigte arabische emirate": "AE",
    "isr": "IL", "israel": "IL",
    "lux": "LU", "luxembourg": "LU", "luxemburg": "LU",
    "lie": "LI", "liechtenstein": "LI",
    "rou": "RO", "romania": "RO", "rumänien": "RO", "rumaenien": "RO",
    "bgr": "BG", "bulgaria": "BG", "bulgarien": "BG",
    "hrv": "HR", "croatia": "HR", "kroatien": "HR",
    "svk": "SK", "slovakia": "SK", "slowakei": "SK",
    "svn": "SI", "slovenia": "SI", "slowenien": "SI",
    "ukr": "UA", "ukraine": "UA",
    "est": "EE", "estonia": "EE", "estland": "EE",
    "lva": "LV", "latvia": "LV", "lettland": "LV",
    "ltu": "LT", "lithuania": "LT", "litauen": "LT",
    "isl": "IS", "iceland": "IS", "island": "IS",
    "cyp": "CY", "cyprus": "CY", "zypern": "CY",
    "mlt": "MT", "malta": "MT",
    "egy": "EG", "egypt": "EG", "ägypten": "EG", "aegypten": "EG",
    "mar": "MA", "morocco": "MA", "marokko": "MA",
    "tha": "TH", "thailand": "TH",
    "vnm": "VN", "vietnam": "VN",
    "idn": "ID", "indonesia": "ID", "indonesien": "ID",
    "mys": "MY", "malaysia": "MY",
    "phl": "PH", "philippines": "PH", "philippinen": "PH",
    "pak": "PK", "pakistan": "PK",
    "bgd": "BD", "bangladesh": "BD", "bangladesch": "BD",
    "twn": "TW", "taiwan": "TW",
    "hkg": "HK", "hong kong": "HK", "hongkong": "HK",
    "sau": "SA", "saudi arabia": "SA", "saudi-arabien": "SA",
    "qat": "QA", "qatar": "QA", "katar": "QA", "qatar": "QA",
    "kwt": "KW", "kuwait": "KW",
    "per": "PE", "peru": "PE",
    "ven": "VE", "venezuela": "VE",
    "ecu": "EC", "ecuador": "EC",
}

def normalize_country(val):
    if pd.isna(val):
        return "UNKNOWN"
    s = str(val).strip()
    if not s:
        return "UNKNOWN"
    s_lower = s.lower()
    if s_lower in custom_map:
        return custom_map[s_lower]
    s_upper = s.upper()
    if s_upper in valid_iso_alpha2:
        return s_upper
    return "UNKNOWN"

df["country"] = df["country"].apply(normalize_country)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)