import pandas as pd
import numpy as np

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/cleaning_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/cleaning_hard/output.parquet"

df = pd.read_parquet(input_path)

country_map = {
    "de": "DE", "deu": "DE", "deutschland": "DE", "germany": "DE", "german": "DE", "d": "DE",
    "at": "AT", "aut": "AT", "österreich": "AT", "oesterreich": "AT", "austria": "AT",
    "ch": "CH", "che": "CH", "schweiz": "CH", "switzerland": "CH", "suisse": "CH", "svizzera": "CH",
    "us": "US", "usa": "US", "united states": "US", "united states of america": "US", "vereinigte staaten": "US", "america": "US",
    "gb": "GB", "uk": "GB", "united kingdom": "GB", "great britain": "GB", "grossbritannien": "GB", "großbritannien": "GB", "england": "GB",
    "fr": "FR", "fra": "FR", "frankreich": "FR", "france": "FR",
    "it": "IT", "ita": "IT", "italien": "IT", "italy": "IT", "italia": "IT",
    "es": "ES", "esp": "ES", "spanien": "ES", "spain": "ES", "espana": "ES", "españa": "ES",
    "nl": "NL", "nld": "NL", "niederlande": "NL", "netherlands": "NL", "holland": "NL",
    "be": "BE", "bel": "BE", "belgien": "BE", "belgium": "BE",
    "lu": "LU", "lux": "LU", "luxemburg": "LU", "luxembourg": "LU",
    "pl": "PL", "pol": "PL", "polen": "PL", "poland": "PL",
    "cz": "CZ", "cze": "CZ", "tschechien": "CZ", "czech republic": "CZ", "czechia": "CZ",
    "dk": "DK", "dnk": "DK", "dänemark": "DK", "daenemark": "DK", "denmark": "DK",
    "se": "SE", "swe": "SE", "schweden": "SE", "sweden": "SE",
    "no": "NO", "nor": "NO", "norwegen": "NO", "norway": "NO",
    "fi": "FI", "fin": "FI", "finnland": "FI", "finland": "FI",
    "pt": "PT", "prt": "PT", "portugal": "PT",
    "ie": "IE", "irl": "IE", "irland": "IE", "ireland": "IE",
    "gr": "GR", "grc": "GR", "griechenland": "GR", "greece": "GR",
    "hu": "HU", "hun": "HU", "ungarn": "HU", "hungary": "HU",
    "ro": "RO", "rou": "RO", "rumänien": "RO", "rumaenien": "RO", "romania": "RO",
    "bg": "BG", "bgr": "BG", "bulgarien": "BG", "bulgaria": "BG",
    "hr": "HR", "hrv": "HR", "kroatien": "HR", "croatia": "HR",
    "si": "SI", "svn": "SI", "slowenien": "SI", "slovenia": "SI",
    "sk": "SK", "svk": "SK", "slowakei": "SK", "slovakia": "SK",
    "lt": "LT", "ltu": "LT", "litauen": "LT", "lithuania": "LT",
    "lv": "LV", "lva": "LV", "lettland": "LV", "latvia": "LV",
    "ee": "EE", "est": "EE", "estland": "EE", "estonia": "EE",
    "ru": "RU", "rus": "RU", "russland": "RU", "russia": "RU",
    "ua": "UA", "ukr": "UA", "ukraine": "UA",
    "tr": "TR", "tur": "TR", "türkei": "TR", "tuerkei": "TR", "turkey": "TR",
    "ch": "CH",
    "ca": "CA", "can": "CA", "kanada": "CA", "canada": "CA",
    "mx": "MX", "mex": "MX", "mexiko": "MX", "mexico": "MX",
    "br": "BR", "bra": "BR", "brasilien": "BR", "brazil": "BR",
    "ar": "AR", "arg": "AR", "argentinien": "AR", "argentina": "AR",
    "cn": "CN", "chn": "CN", "china": "CN",
    "jp": "JP", "jpn": "JP", "japan": "JP",
    "kr": "KR", "kor": "KR", "südkorea": "KR", "suedkorea": "KR", "south korea": "KR",
    "in": "IN", "ind": "IN", "indien": "IN", "india": "IN",
    "au": "AU", "aus": "AU", "australien": "AU", "australia": "AU",
    "nz": "NZ", "nzl": "NZ", "neuseeland": "NZ", "new zealand": "NZ",
    "za": "ZA", "zaf": "ZA", "südafrika": "ZA", "suedafrika": "ZA", "south africa": "ZA",
    "eg": "EG", "egy": "EG", "ägypten": "EG", "aegypten": "EG", "egypt": "EG",
    "il": "IL", "isr": "IL", "israel": "IL",
    "sa": "SA", "sau": "SA", "saudi arabien": "SA", "saudi arabia": "SA",
    "ae": "AE", "are": "AE", "vereinigte arabische emirate": "AE", "united arab emirates": "AE",
    "ch": "CH",
    "cy": "CY", "cyp": "CY", "zypern": "CY", "cyprus": "CY",
    "mt": "MT", "mlt": "MT", "malta": "MT",
    "is": "IS", "isl": "IS", "island": "IS", "iceland": "IS",
    "li": "LI", "lie": "LI", "liechtenstein": "LI",
    "mc": "MC", "mco": "MC", "monaco": "MC",
    "sm": "SM", "smr": "SM", "san marino": "SM",
    "va": "VA", "vat": "VA", "vatikan": "VA", "vatican": "VA",
    "ad": "AD", "and": "AD", "andorra": "AD",
    "rs": "RS", "srb": "RS", "serbien": "RS", "serbia": "RS",
    "ba": "BA", "bih": "BA", "bosnien": "BA", "bosnien und herzegowina": "BA", "bosnia and herzegovina": "BA",
    "me": "ME", "mne": "ME", "montenegro": "ME",
    "mk": "MK", "mkd": "MK", "nordmazedonien": "MK", "north macedonia": "MK",
    "al": "AL", "alb": "AL", "albanien": "AL", "albania": "AL",
    "by": "BY", "blr": "BY", "weissrussland": "BY", "weißrussland": "BY", "belarus": "BY",
    "md": "MD", "mda": "MD", "moldawien": "MD", "moldova": "MD",
    "ge": "GE", "geo": "GE", "georgien": "GE", "georgia": "GE",
    "am": "AM", "arm": "AM", "armenien": "AM", "armenia": "AM",
    "az": "AZ", "aze": "AZ", "aserbaidschan": "AZ", "azerbaijan": "AZ",
    "kz": "KZ", "kaz": "KZ", "kasachstan": "KZ", "kazakhstan": "KZ",
    "th": "TH", "tha": "TH", "thailand": "TH",
    "vn": "VN", "vnm": "VN", "vietnam": "VN",
    "id": "ID", "idn": "ID", "indonesien": "ID", "indonesia": "ID",
    "my": "MY", "mys": "MY", "malaysia": "MY",
    "sg": "SG", "sgp": "SG", "singapur": "SG", "singapore": "SG",
    "ph": "PH", "phl": "PH", "philippinen": "PH", "philippines": "PH",
    "pk": "PK", "pak": "PK", "pakistan": "PK",
    "bd": "BD", "bgd": "BD", "bangladesch": "BD", "bangladesh": "BD",
    "cl": "CL", "chl": "CL", "chile": "CL",
    "co": "CO", "col": "CO", "kolumbien": "CO", "colombia": "CO",
    "pe": "PE", "per": "PE", "peru": "PE",
    "ve": "VE", "ven": "VE", "venezuela": "VE",
    "ec": "EC", "ecu": "EC", "ecuador": "EC",
    "uy": "UY", "ury": "UY", "uruguay": "UY",
    "py": "PY", "pry": "PY", "paraguay": "PY",
    "bo": "BO", "bol": "BO", "bolivien": "BO", "bolivia": "BO",
    "cr": "CR", "cri": "CR", "costa rica": "CR",
    "pa": "PA", "pan": "PA", "panama": "PA",
    "cu": "CU", "cub": "CU", "kuba": "CU", "cuba": "CU",
    "do": "DO", "dom": "DO", "dominikanische republik": "DO", "dominican republic": "DO",
    "jm": "JM", "jam": "JM", "jamaika": "JM", "jamaica": "JM",
    "ma": "MA", "mar": "MA", "marokko": "MA", "morocco": "MA",
    "dz": "DZ", "dza": "DZ", "algerien": "DZ", "algeria": "DZ",
    "tn": "TN", "tun": "TN", "tunesien": "TN", "tunisia": TN if False else "TN",
    "ng": "NG", "nga": "NG", "nigeria": "NG",
    "ke": "KE", "ken": "KE", "kenia": "KE", "kenya": "KE",
    "gh": "GH", "gha": "GH", "ghana": "GH",
    "et": "ET", "eth": "ET", "äthiopien": "ET", "aethiopien": "ET", "ethiopia": "ET",
}

def normalize_country(val):
    if pd.isna(val):
        return "UNKNOWN"
    s = str(val).strip().lower()
    if s == "":
        return "UNKNOWN"
    s_clean = s.replace(".", "").replace("_", " ").replace("-", " ").strip()
    if s_clean in country_map:
        return country_map[s_clean]
    # try uppercase 2-letter code check directly
    upper = str(val).strip().upper()
    if len(upper) == 2 and upper.isalpha():
        return upper
    return "UNKNOWN"

df["country"] = df["country"].apply(normalize_country)

df.to_parquet(output_path, index=False)