import pandas as pd
import numpy as np

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_isolated_r4/cleaning_hard/output.parquet"

df = pd.read_parquet(input_path)

country_map = {
    "germany": "DE", "deutschland": "DE", "de": "DE", "ger": "DE", "deu": "DE", "d": "DE",
    "austria": "AT", "österreich": "AT", "oesterreich": "AT", "at": "AT", "aut": "AT",
    "switzerland": "CH", "schweiz": "CH", "ch": "CH", "che": "CH", "suisse": "CH",
    "france": "FR", "frankreich": "FR", "fr": "FR", "fra": "FR",
    "italy": "IT", "italien": "IT", "it": "IT", "ita": "IT",
    "spain": "ES", "spanien": "ES", "es": "ES", "esp": "ES",
    "portugal": "PT", "pt": "PT", "prt": "PT",
    "netherlands": "NL", "niederlande": "NL", "nl": "NL", "nld": "NL", "holland": "NL",
    "belgium": "BE", "belgien": "BE", "be": "BE", "bel": "BE",
    "luxembourg": "LU", "luxemburg": "LU", "lu": "LU", "lux": "LU",
    "united kingdom": "GB", "vereinigtes königreich": "GB", "vereinigtes koenigreich": "GB",
    "uk": "GB", "gb": "GB", "gbr": "GB", "great britain": "GB", "england": "GB", "britain": "GB",
    "ireland": "IE", "irland": "IE", "ie": "IE", "irl": "IE",
    "united states": "US", "vereinigte staaten": "US", "usa": "US", "us": "US", "u.s.a.": "US",
    "u.s.": "US", "america": "US", "vereinigte staaten von amerika": "US",
    "canada": "CA", "kanada": "CA", "ca": "CA", "can": "CA",
    "mexico": "MX", "mexiko": "MX", "mx": "MX", "mex": "MX",
    "brazil": "BR", "brasilien": "BR", "br": "BR", "bra": "BR",
    "argentina": "AR", "argentinien": "AR", "ar": "AR", "arg": "AR",
    "china": "CN", "cn": "CN", "chn": "CN",
    "japan": "JP", "jp": "JP", "jpn": "JP",
    "south korea": "KR", "südkorea": "KR", "suedkorea": "KR", "kr": "KR", "kor": "KR",
    "india": "IN", "indien": "IN", "in": "IN", "ind": "IN",
    "russia": "RU", "russland": "RU", "ru": "RU", "rus": "RU",
    "poland": "PL", "polen": "PL", "pl": "PL", "pol": "PL",
    "sweden": "SE", "schweden": "SE", "se": "SE", "swe": "SE",
    "norway": "NO", "norwegen": "NO", "no": "NO", "nor": "NO",
    "denmark": "DK", "dänemark": "DK", "daenemark": "DK", "dk": "DK", "dnk": "DK",
    "finland": "FI", "finnland": "FI", "fi": "FI", "fin": "FI",
    "greece": "GR", "griechenland": "GR", "gr": "GR", "grc": "GR",
    "turkey": "TR", "türkei": "TR", "tuerkei": "TR", "tr": "TR", "tur": "TR",
    "australia": "AU", "australien": "AU", "au": "AU", "aus": "AU",
    "new zealand": "NZ", "neuseeland": "NZ", "nz": "NZ", "nzl": "NZ",
    "south africa": "ZA", "südafrika": "ZA", "suedafrika": "ZA", "za": "ZA", "zaf": "ZA",
    "egypt": "EG", "ägypten": "EG", "aegypten": "EG", "eg": "EG", "egy": "EG",
    "czech republic": "CZ", "tschechien": "CZ", "cz": "CZ", "cze": "CZ", "czechia": "CZ",
    "hungary": "HU", "ungarn": "HU", "hu": "HU", "hun": "HU",
    "romania": "RO", "rumänien": "RO", "rumaenien": "RO", "ro": "RO", "rou": "RO",
    "bulgaria": "BG", "bulgarien": "BG", "bg": "BG", "bgr": "BG",
    "croatia": "HR", "kroatien": "HR", "hr": "HR", "hrv": "HR",
    "slovenia": "SI", "slowenien": "SI", "si": "SI", "svn": "SI",
    "slovakia": "SK", "slowakei": "SK", "sk": "SK", "svk": "SK",
    "ukraine": "UA", "ua": "UA", "ukr": "UA",
    "iceland": "IS", "island": "IS", "is": "IS", "isl": "IS",
    "china prc": "CN",
    "united arab emirates": "AE", "vereinigte arabische emirate": "AE", "ae": "AE", "are": "AE", "uae": "AE",
    "saudi arabia": "SA", "saudi-arabien": "SA", "sa": "SA", "sau": "SA",
    "israel": "IL", "il": "IL", "isr": "IL",
    "thailand": "TH", "th": "TH", "tha": "TH",
    "vietnam": "VN", "vn": "VN", "vnm": "VN",
    "indonesia": "ID", "indonesien": "ID", "id": "ID", "idn": "ID",
    "malaysia": "MY", "my": "MY", "mys": "MY",
    "philippines": "PH", "philippinen": "PH", "ph": "PH", "phl": "PH",
    "singapore": "SG", "singapur": "SG", "sg": "SG", "sgp": "SG",
    "pakistan": "PK", "pk": "PK", "pak": "PK",
    "bangladesh": "BD", "bd": "BD", "bgd": "BD",
    "nigeria": "NG", "ng": "NG", "nga": "NG",
    "kenya": "KE", "kenia": "KE", "ke": "KE", "ken": "KE",
    "morocco": "MA", "marokko": "MA", "ma": "MA", "mar": "MA",
    "chile": "CL", "cl": "CL", "chl": "CL",
    "colombia": "CO", "kolumbien": "CO", "co": "CO", "col": "CO",
    "peru": "PE", "pe": "PE", "per": "PE",
    "venezuela": "VE", "ve": "VE", "ven": "VE",
    "cuba": "CU", "kuba": "CU", "cu": "CU", "cub": "CU",
}

def normalize_country(val):
    if pd.isna(val):
        return "UNKNOWN"
    s = str(val).strip().lower()
    s = s.replace(".", "").replace("_", " ").replace("-", " ")
    s = " ".join(s.split())
    if s in country_map:
        return country_map[s]
    s_nospace = s.replace(" ", "")
    if s_nospace in country_map:
        return country_map[s_nospace]
    if len(s) == 2 and s.isalpha():
        upper = s.upper()
        valid_codes = set(country_map.values())
        if upper in valid_codes:
            return upper
    return "UNKNOWN"

df["country"] = df["country"].apply(normalize_country)

df.to_parquet(output_path, index=False)