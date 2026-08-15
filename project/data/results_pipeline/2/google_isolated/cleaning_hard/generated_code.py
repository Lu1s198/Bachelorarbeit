import os
import pandas as pd

input_file = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_medium/output.parquet"
output_file = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_isolated/cleaning_hard/output.parquet"

df = pd.read_parquet(input_file)

country_map = {
    "de": "DE", "deu": "DE", "germany": "DE", "deutschland": "DE", "ger": "DE", "bundesrepublik deutschland": "DE",
    "us": "US", "usa": "US", "united states": "US", "united states of america": "US", "vereinigte staaten": "US", "vereinigte staaten von amerika": "US", "us of a": "US",
    "gb": "GB", "gbr": "GB", "uk": "GB", "united kingdom": "GB", "great britain": "GB", "vereinigtes königreich": "GB", "vereinigtes koenigreich": "GB", "grossbritannien": "GB", "großbritannien": "GB", "england": "GB", "eng": "GB",
    "at": "AT", "aut": "AT", "austria": "AT", "österreich": "AT", "oesterreich": "AT",
    "ch": "CH", "che": "CH", "switzerland": "CH", "schweiz": "CH", "suisse": "CH", "svizzera": "CH",
    "fr": "FR", "fra": "FR", "france": "FR", "frankreich": "FR",
    "it": "IT", "ita": "IT", "italy": "IT", "italien": "IT",
    "es": "ES", "esp": "ES", "spain": "ES", "spanien": "ES",
    "nl": "NL", "nld": "NL", "netherlands": "NL", "niederlande": "NL", "holland": "NL",
    "be": "BE", "bel": "BE", "belgium": "BE", "belgien": "BE",
    "pl": "PL", "pol": "PL", "poland": "PL", "polen": "PL",
    "cz": "CZ", "cze": "CZ", "czech republic": "CZ", "czechia": "CZ", "tschechien": "CZ", "tschechische republik": "CZ",
    "dk": "DK", "dnk": "DK", "denmark": "DK", "dänemark": "DK", "daenemark": "DK",
    "se": "SE", "swe": "SE", "sweden": "SE", "schweden": "SE",
    "no": "NO", "nor": "NO", "norway": "NO", "norwegen": "NO",
    "fi": "FI", "fin": "FI", "finland": "FI", "finnland": "FI",
    "pt": "PT", "prt": "PT", "portugal": "PT",
    "gr": "GR", "grc": "GR", "greece": "GR", "griechenland": "GR",
    "ie": "IE", "irl": "IE", "ireland": "IE", "irland": "IE",
    "ca": "CA", "can": "CA", "canada": "CA", "kanada": "CA",
    "au": "AU", "aus": "AU", "australia": "AU", "australien": "AU",
    "nz": "NZ", "nzl": "NZ", "new zealand": "NZ", "neuseeland": "NZ",
    "jp": "JP", "jpn": "JP", "japan": "JP",
    "cn": "CN", "chn": "CN", "china": "CN",
    "in": "IN", "ind": "IN", "india": "IN", "indien": "IN",
    "br": "BR", "bra": "BR", "brazil": "BR", "brasilien": "BR",
    "mx": "MX", "mex": "MX", "mexico": "MX", "mexiko": "MX",
    "ru": "RU", "rus": "RU", "russia": "RU", "russland": "RU", "russian federation": "RU",
    "tr": "TR", "tur": "TR", "turkey": "TR", "türkei": "TR", "tuerkei": "TR", "türkiye": "TR",
    "za": "ZA", "zaf": "ZA", "south africa": "ZA", "südafrika": "ZA", "suedafrika": "ZA",
    "hu": "HU", "hun": "HU", "hungary": "HU", "ungarn": "HU",
    "ro": "RO", "rou": "RO", "romania": "RO", "rumänien": "RO", "rumaenien": "RO",
    "bg": "BG", "bgr": "BG", "bulgaria": "BG", "bulgarien": "BG",
    "hr": "HR", "hrv": "HR", "croatia": "HR", "kroatien": "HR",
    "sk": "SK", "svk": "SK", "slovakia": "SK", "slowakei": "SK",
    "si": "SI", "svn": "SI", "slovenia": "SI", "slowenien": "SI",
    "ua": "UA", "ukr": "UA", "ukraine": "UA",
    "il": "IL", "isr": "IL", "israel": "IL",
    "eg": "EG", "egy": "EG", "egypt": "EG", "ägypten": "EG", "aegypten": "EG",
    "ma": "MA", "mar": "MA", "morocco": "MA", "marokko": "MA",
    "th": "TH", "tha": "TH", "thailand": "TH",
    "vn": "VN", "vnm": "VN", "vietnam": "VN",
    "kr": "KR", "kor": "KR", "south korea": "KR", "südkorea": "KR", "suedkorea": "KR", "korea": "KR",
    "ar": "AR", "arg": "AR", "argentina": "AR", "argentinien": "AR",
    "cl": "CL", "chl": "CL", "chile": "CL",
    "co": "CO", "col": "CO", "colombia": "CO", "kolumbien": "CO",
    "pe": "PE", "per": "PE", "peru": "PE",
    "sg": "SG", "sgp": "SG", "singapore": "SG", "singapur": "SG",
    "ae": "AE", "are": "AE", "uae": "AE", "united arab emirates": "AE", "vereinigte arabische emirate": "AE",
    "sa": "SA", "sau": "SA", "saudi arabia": "SA", "saudi-arabien": "SA",
    "lu": "LU", "lux": "LU", "luxembourg": "LU", "luxemburg": "LU",
    "li": "LI", "lie": "LI", "liechtenstein": "LI",
    "is": "IS", "isl": "IS", "iceland": "IS", "island": "IS"
}

def map_country(val):
    if pd.isna(val):
        return "UNKNOWN"
    s = str(val).strip().lower()
    if not s:
        return "UNKNOWN"
    return country_map.get(s, "UNKNOWN")

df["country"] = df["country"].apply(map_country)

os.makedirs(os.path.dirname(output_file), exist_ok=True)
df.to_parquet(output_file, index=False)