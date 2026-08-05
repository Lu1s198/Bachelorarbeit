import pandas as pd
import numpy as np

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/cleaning_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/cleaning_hard/output.parquet"

df = pd.read_parquet(input_path)

country_map = {
    "germany": "DE", "deutschland": "DE", "de": "DE", "deu": "DE", "ger": "DE",
    "allemagne": "DE", "bundesrepublik deutschland": "DE",
    "austria": "AT", "oesterreich": "AT", "österreich": "AT", "at": "AT", "aut": "AT",
    "switzerland": "CH", "schweiz": "CH", "suisse": "CH", "ch": "CH", "che": "CH",
    "confoederatio helvetica": "CH",
    "france": "FR", "frankreich": "FR", "fr": "FR", "fra": "FR",
    "united kingdom": "GB", "grossbritannien": "GB", "großbritannien": "GB",
    "vereinigtes koenigreich": "GB", "vereinigtes königreich": "GB",
    "uk": "GB", "gb": "GB", "gbr": "GB", "england": "GB", "britain": "GB",
    "united states": "US", "united states of america": "US", "usa": "US",
    "us": "US", "u.s.a.": "US", "u.s.": "US", "vereinigte staaten": "US",
    "vereinigte staaten von amerika": "US", "amerika": "US",
    "italy": "IT", "italien": "IT", "it": "IT", "ita": "IT", "italia": "IT",
    "spain": "ES", "spanien": "ES", "es": "ES", "esp": "ES", "espana": "ES", "españa": "ES",
    "netherlands": "NL", "niederlande": "NL", "nl": "NL", "nld": "NL", "holland": "NL",
    "belgium": "BE", "belgien": "BE", "be": "BE", "bel": "BE",
    "poland": "PL", "polen": "PL", "pl": "PL", "pol": "PL",
    "portugal": "PT", "pt": "PT", "prt": "PT",
    "sweden": "SE", "schweden": "SE", "se": "SE", "swe": "SE",
    "norway": "NO", "norwegen": "NO", "no": "NO", "nor": "NO",
    "denmark": "DK", "daenemark": "DK", "dänemark": "DK", "dk": "DK", "dnk": "DK",
    "finland": "FI", "finnland": "FI", "fi": "FI", "fin": "FI",
    "ireland": "IE", "irland": "IE", "ie": "IE", "irl": "IE",
    "luxembourg": "LU", "luxemburg": "LU", "lu": "LU", "lux": "LU",
    "greece": "GR", "griechenland": "GR", "gr": "GR", "grc": "GR",
    "czech republic": "CZ", "tschechien": "CZ", "cz": "CZ", "cze": "CZ",
    "czechia": "CZ",
    "hungary": "HU", "ungarn": "HU", "hu": "HU", "hun": "HU",
    "slovakia": "SK", "slowakei": "SK", "sk": "SK", "svk": "SK",
    "slovenia": "SI", "slowenien": "SI", "si": "SI", "svn": "SI",
    "croatia": "HR", "kroatien": "HR", "hr": "HR", "hrv": "HR",
    "romania": "RO", "rumaenien": "RO", "rumänien": "RO", "ro": "RO", "rou": "RO",
    "bulgaria": "BG", "bulgarien": "BG", "bg": "BG", "bgr": "BG",
    "russia": "RU", "russland": "RU", "ru": "RU", "rus": "RU",
    "china": "CN", "cn": "CN", "chn": "CN",
    "japan": "JP", "jp": "JP", "jpn": "JP",
    "south korea": "KR", "suedkorea": "KR", "südkorea": "KR", "kr": "KR", "kor": "KR",
    "korea": "KR",
    "india": "IN", "indien": "IN", "in": "IN", "ind": "IN",
    "canada": "CA", "kanada": "CA", "ca": "CA", "can": "CA",
    "australia": "AU", "australien": "AU", "au": "AU", "aus": "AU",
    "brazil": "BR", "brasilien": "BR", "br": "BR", "bra": "BR",
    "mexico": "MX", "mexiko": "MX", "mx": "MX", "mex": "MX",
    "argentina": "AR", "argentinien": "AR", "ar": "AR", "arg": "AR",
    "south africa": "ZA", "suedafrika": "ZA", "südafrika": "ZA", "za": "ZA", "zaf": "ZA",
    "turkey": "TR", "tuerkei": "TR", "türkei": "TR", "tr": "TR", "tur": "TR",
    "ukraine": "UA", "ua": "UA", "ukr": "UA",
    "new zealand": "NZ", "neuseeland": "NZ", "nz": "NZ", "nzl": "NZ",
    "iceland": "IS", "island": "IS", "is": "IS", "isl": "IS",
    "estonia": "EE", "estland": "EE", "ee": "EE", "est": "EE",
    "latvia": "LV", "lettland": "LV", "lv": "LV", "lva": "LV",
    "lithuania": "LT", "litauen": "LT", "lt": "LT", "ltu": "LT",
    "serbia": "RS", "serbien": "RS", "rs": "RS", "srb": "RS",
    "china (prc)": "CN",
    "china, volksrepublik": "CN",
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
    # try uppercase 2-letter code directly
    upper = str(val).strip().upper()
    if len(upper) == 2 and upper.isalpha():
        # accept as-is, assume valid ISO code
        return upper
    return "UNKNOWN"

df["country"] = df["country"].apply(normalize_country)

df.to_parquet(output_path, index=False)