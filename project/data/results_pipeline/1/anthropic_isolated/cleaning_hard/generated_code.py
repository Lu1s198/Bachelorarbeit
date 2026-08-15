import pandas as pd
import numpy as np

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/_reference/cleaning_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic_isolated/cleaning_hard/output.parquet"

df = pd.read_parquet(input_path)

country_map = {
    "germany": "DE", "deutschland": "DE", "de": "DE", "deu": "DE", "ger": "DE", "d": "DE",
    "bundesrepublik deutschland": "DE",
    "austria": "AT", "oesterreich": "AT", "österreich": "AT", "at": "AT", "aut": "AT",
    "switzerland": "CH", "schweiz": "CH", "suisse": "CH", "svizzera": "CH", "ch": "CH", "che": "CH",
    "confoederatio helvetica": "CH",
    "united states": "US", "united states of america": "US", "usa": "US", "us": "US",
    "vereinigte staaten": "US", "vereinigte staaten von amerika": "US", "america": "US", "usa.": "US",
    "united kingdom": "GB", "uk": "GB", "great britain": "GB", "gb": "GB", "gbr": "GB",
    "vereinigtes koenigreich": "GB", "vereinigtes königreich": "GB", "england": "GB", "britain": "GB",
    "france": "FR", "frankreich": "FR", "fr": "FR", "fra": "FR",
    "italy": "IT", "italien": "IT", "it": "IT", "ita": "IT",
    "spain": "ES", "spanien": "ES", "es": "ES", "esp": "ES",
    "portugal": "PT", "pt": "PT", "prt": "PT",
    "netherlands": "NL", "niederlande": "NL", "nl": "NL", "nld": "NL", "holland": "NL",
    "belgium": "BE", "belgien": "BE", "be": "BE", "bel": "BE",
    "luxembourg": "LU", "luxemburg": "LU", "lu": "LU", "lux": "LU",
    "poland": "PL", "polen": "PL", "pl": "PL", "pol": "PL",
    "czech republic": "CZ", "tschechien": "CZ", "cz": "CZ", "cze": "CZ", "czechia": "CZ",
    "slovakia": "SK", "slowakei": "SK", "sk": "SK", "svk": "SK",
    "hungary": "HU", "ungarn": "HU", "hu": "HU", "hun": "HU",
    "denmark": "DK", "daenemark": "DK", "dänemark": "DK", "dk": "DK", "dnk": "DK",
    "sweden": "SE", "schweden": "SE", "se": "SE", "swe": "SE",
    "norway": "NO", "norwegen": "NO", "no": "NO", "nor": "NO",
    "finland": "FI", "finnland": "FI", "fi": "FI", "fin": "FI",
    "iceland": "IS", "island": "IS", "is": "IS", "isl": "IS",
    "ireland": "IE", "irland": "IE", "ie": "IE", "irl": "IE",
    "greece": "GR", "griechenland": "GR", "gr": "GR", "grc": "GR",
    "turkey": "TR", "tuerkei": "TR", "türkei": "TR", "tr": "TR", "tur": "TR",
    "russia": "RU", "russland": "RU", "ru": "RU", "rus": "RU", "russian federation": "RU",
    "ukraine": "UA", "ua": "UA", "ukr": "UA",
    "china": "CN", "cn": "CN", "chn": "CN",
    "japan": "JP", "jp": "JP", "jpn": "JP",
    "south korea": "KR", "suedkorea": "KR", "südkorea": "KR", "kr": "KR", "kor": "KR",
    "india": "IN", "indien": "IN", "in": "IN", "ind": "IN",
    "brazil": "BR", "brasilien": "BR", "br": "BR", "bra": "BR",
    "canada": "CA", "kanada": "CA", "ca": "CA", "can": "CA",
    "mexico": "MX", "mexiko": "MX", "mx": "MX", "mex": "MX",
    "australia": "AU", "australien": "AU", "au": "AU", "aus": "AU",
    "new zealand": "NZ", "neuseeland": "NZ", "nz": "NZ", "nzl": "NZ",
    "south africa": "ZA", "suedafrika": "ZA", "südafrika": "ZA", "za": "ZA", "zaf": "ZA",
    "egypt": "EG", "aegypten": "EG", "ägypten": "EG", "eg": "EG", "egy": "EG",
    "argentina": "AR", "argentinien": "AR", "ar": "AR", "arg": "AR",
    "chile": "CL", "cl": "CL", "chl": "CL",
    "colombia": "CO", "kolumbien": "CO", "co": "CO", "col": "CO",
    "peru": "PE", "pe": "PE", "per": "PE",
    "venezuela": "VE", "ve": "VE", "ven": "VE",
    "romania": "RO", "rumaenien": "RO", "rumänien": "RO", "ro": "RO", "rou": "RO",
    "bulgaria": "BG", "bulgarien": "BG", "bg": "BG", "bgr": "BG",
    "croatia": "HR", "kroatien": "HR", "hr": "HR", "hrv": "HR",
    "serbia": "RS", "serbien": "RS", "rs": "RS", "srb": "RS",
    "slovenia": "SI", "slowenien": "SI", "si": "SI", "svn": "SI",
    "estonia": "EE", "estland": "EE", "ee": "EE", "est": "EE",
    "latvia": "LV", "lettland": "LV", "lv": "LV", "lva": "LV",
    "lithuania": "LT", "litauen": "LT", "lt": "LT", "ltu": "LT",
    "belarus": "BY", "weissrussland": "BY", "weißrussland": "BY", "by": "BY", "blr": "BY",
    "portugal republic": "PT",
    "thailand": "TH", "th": "TH", "tha": "TH",
    "vietnam": "VN", "vn": "VN", "vnm": "VN",
    "indonesia": "ID", "indonesien": "ID", "id": "ID", "idn": "ID",
    "malaysia": "MY", "my": "MY", "mys": "MY",
    "singapore": "SG", "singapur": "SG", "sg": "SG", "sgp": "SG",
    "philippines": "PH", "philippinen": "PH", "ph": "PH", "phl": "PH",
    "pakistan": "PK", "pk": "PK", "pak": "PK",
    "bangladesh": "BD", "bd": "BD", "bgd": "BD",
    "israel": "IL", "il": "IL", "isr": "IL",
    "saudi arabia": "SA", "saudi-arabien": "SA", "sa": "SA", "sau": "SA",
    "united arab emirates": "AE", "vereinigte arabische emirate": "AE", "ae": "AE", "are": "AE", "uae": "AE",
    "morocco": "MA", "marokko": "MA", "ma": "MA", "mar": "MA",
    "algeria": "DZ", "algerien": "DZ", "dz": "DZ", "dza": "DZ",
    "tunisia": "TN", "tunesien": "TN", "tn": "TN", "tun": "TN",
    "nigeria": "NG", "ng": "NG", "nga": "NG",
    "kenya": "KE", "kenia": "KE", "ke": "KE", "ken": "KE",
    "cyprus": "CY", "zypern": "CY", "cy": "CY", "cyp": "CY",
    "malta": "MT", "mt": "MT", "mlt": "MT",
    "monaco": "MC", "mc": "MC", "mco": "MC",
    "liechtenstein": "LI", "li": "LI", "lie": "LI",
    "andorra": "AD", "ad": "AD", "and": "AD",
    "san marino": "SM", "sm": "SM", "smr": "SM",
    "vatican": "VA", "vatikan": "VA", "va": "VA", "vat": "VA",
    "bosnia and herzegovina": "BA", "bosnien": "BA", "ba": "BA", "bih": "BA",
    "north macedonia": "MK", "mazedonien": "MK", "mk": "MK", "mkd": "MK",
    "albania": "AL", "albanien": "AL", "al": "AL", "alb": "AL",
    "montenegro": "ME", "me": "ME", "mne": "ME",
    "moldova": "MD", "moldawien": "MD", "md": "MD", "mda": "MD",
    "georgia": "GE", "georgien": "GE", "ge": "GE", "geo": "GE",
    "armenia": "AM", "armenien": "AM", "am": "AM", "arm": "AM",
    "azerbaijan": "AZ", "aserbaidschan": "AZ", "az": "AZ", "aze": "AZ",
    "kazakhstan": "KZ", "kasachstan": "KZ", "kz": "KZ", "kaz": "KZ",
    "uzbekistan": "UZ", "usbekistan": "UZ", "uz": "UZ", "uzb": "UZ",
}

def normalize_country(val):
    if pd.isna(val):
        return "UNKNOWN"
    s = str(val).strip().lower()
    s = s.replace(".", "").replace(",", "")
    if s == "":
        return "UNKNOWN"
    if s in country_map:
        return country_map[s]
    s_upper = str(val).strip().upper()
    if len(s_upper) == 2 and s_upper.isalpha():
        for k, v in country_map.items():
            if v == s_upper:
                return v
    return "UNKNOWN"

df["country"] = df["country"].apply(normalize_country)

df.to_parquet(output_path, index=False)