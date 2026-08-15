import os
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/_reference/cleaning_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google_isolated/cleaning_hard/output.parquet"

df = pd.read_parquet(input_path)

country_map = {
    "de": "DE", "deu": "DE", "ger": "DE", "deutschland": "DE", "germany": "DE", "allemagne": "DE",
    "us": "US", "usa": "US", "united states": "US", "united states of america": "US", "vereinige staaten": "US", "vereinigte staaten": "US", "vereinigte staaten von amerika": "US", "america": "US",
    "gb": "GB", "gbr": "GB", "uk": "GB", "united kingdom": "GB", "great britain": "GB", "großbritannien": "GB", "grossbritannien": "GB", "england": "GB", "scotland": "GB", "wales": "GB",
    "fr": "FR", "fra": "FR", "frankreich": "FR", "france": "FR",
    "at": "AT", "aut": "AT", "österreich": "AT", "oesterreich": "AT", "austria": "AT",
    "ch": "CH", "che": "CH", "schweiz": "CH", "switzerland": "CH", "suisse": "CH",
    "it": "IT", "ita": "IT", "italien": "IT", "italy": "IT",
    "es": "ES", "esp": "ES", "spanien": "ES", "spain": "ES",
    "nl": "NL", "nld": "NL", "niederlande": "NL", "netherlands": "NL", "holland": "NL",
    "be": "BE", "bel": "BE", "belgien": "BE", "belgium": "BE",
    "pl": "PL", "pol": "PL", "polen": "PL", "poland": "PL",
    "cz": "CZ", "cze": "CZ", "tschechien": "CZ", "czech republic": "CZ", "czechia": "CZ",
    "dk": "DK", "dnk": "DK", "dänemark": "DK", "daenemark": "DK", "denmark": "DK",
    "se": "SE", "swe": "SE", "schweden": "SE", "sweden": "SE",
    "no": "NO", "nor": "NO", "norwegen": "NO", "norway": "NO",
    "fi": "FI", "fin": "FI", "finnland": "FI", "finland": "FI",
    "pt": "PT", "prt": "PT", "portugal": "PT",
    "gr": "GR", "grc": "GR", "griechenland": "GR", "greece": "GR",
    "ie": "IE", "irl": "IE", "irland": "IE", "ireland": "IE",
    "ca": "CA", "can": "CA", "kanada": "CA", "canada": "CA",
    "au": "AU", "aus": "AU", "australien": "AU", "australia": "AU",
    "cn": "CN", "chn": "CN", "china": "CN",
    "jp": "JP", "jpn": "JP", "japan": "JP",
    "in": "IN", "ind": "IN", "indien": "IN", "india": "IN",
    "br": "BR", "bra": "BR", "brasilien": "BR", "brazil": "BR",
    "ru": "RU", "rus": "RU", "russland": "RU", "russia": "RU",
    "mx": "MX", "mex": "MX", "mexiko": "MX", "mexico": "MX",
    "za": "ZA", "zaf": "ZA", "südafrika": "ZA", "suedafrika": "ZA", "south africa": "ZA",
    "tr": "TR", "tur": "TR", "türkei": "TR", "tuerkei": "TR", "turkey": "TR", "türkiye": "TR",
    "lu": "LU", "lux": "LU", "luxemburg": "LU", "luxembourg": "LU",
    "li": "LI", "lie": "LI", "liechtenstein": "LI",
    "hu": "HU", "hun": "HU", "ungarn": "HU", "hungary": "HU",
    "ro": "RO", "rou": "RO", "rumänien": "RO", "rumaenien": "RO", "romania": "RO",
    "bg": "BG", "bgr": "BG", "bulgarien": "BG", "bulgaria": "BG",
    "hr": "HR", "hrv": "HR", "kroatien": "HR", "croatia": "HR",
    "si": "SI", "svn": "SI", "slowenien": "SI", "slovenia": "SI",
    "sk": "SK", "svk": "SK", "slowakei": "SK", "slovakia": "SK",
    "ee": "EE", "est": "EE", "estland": "EE", "estonia": "EE",
    "lv": "LV", "lva": "LV", "lettland": "LV", "latvia": "LV",
    "lt": "LT", "ltu": "LT", "litauen": "LT", "lithuania": "LT",
    "ua": "UA", "ukr": "UA", "ukraine": "UA",
    "by": "BY", "blr": "BY", "weißrussland": "BY", "weissrussland": "BY", "belarus": "BY",
    "il": "IL", "isr": "IL", "israel": "IL",
    "eg": "EG", "egy": "EG", "ägypten": "EG", "aegypten": "EG", "egypt": "EG",
    "ar": "AR", "arg": "AR", "argentinien": "AR", "argentina": "AR",
    "cl": "CL", "chl": "CL", "chile": "CL",
    "co": "CO", "col": "CO", "kolumbien": "CO", "colombia": "CO",
    "nz": "NZ", "nzl": "NZ", "neuseeland": "NZ", "new zealand": "NZ",
    "sg": "SG", "sgp": "SG", "singapur": "SG", "singapore": "SG",
    "kr": "KR", "kor": "KR", "südkorea": "KR", "suedkorea": "KR", "south korea": "KR", "korea": "KR",
    "th": "TH", "tha": "TH", "thailand": "TH",
    "vn": "VN", "vnm": "VN", "vietnam": "VN",
    "id": "ID", "idn": "ID", "indonesien": "ID", "indonesia": "ID", "id": "ID",
    "ae": "AE", "are": "AE", "vae": "AE", "uae": "AE", "vereinigte arabische emirate": "AE", "united arab emirates": "AE",
    "sa": "SA", "sau": "SA", "saudi-arabien": "SA", "saudi arabia": "SA", "saudi arabien": "SA",
    "cy": "CY", "cyp": "CY", "zypern": "CY", "cyprus": "CY",
    "mt": "MT", "mlt": "MT", "malta": "MT", "is": "IS", "isl": "IS", "island": "IS", "iceland": "IS"
}

def clean_country(val):
    if pd.isna(val):
        return "UNKNOWN"
    s = str(val).strip().lower()
    return country_map.get(s, "UNKNOWN")

df["country"] = df["country"].apply(clean_country)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)