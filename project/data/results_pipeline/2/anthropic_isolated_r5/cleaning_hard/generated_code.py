import pandas as pd
import numpy as np

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_isolated_r5/cleaning_hard/output.parquet"

df = pd.read_parquet(input_path)

country_map = {
    "de": "DE", "deutschland": "DE", "germany": "DE", "deu": "DE", "ger": "DE", "d": "DE",
    "at": "AT", "österreich": "AT", "oesterreich": "AT", "austria": "AT", "aut": "AT",
    "ch": "CH", "schweiz": "CH", "switzerland": "CH", "svizzera": "CH", "suisse": "CH", "che": "CH",
    "us": "US", "usa": "US", "united states": "US", "united states of america": "US", "vereinigte staaten": "US", "vereinigte staaten von amerika": "US", "usa.": "US",
    "uk": "GB", "gb": "GB", "united kingdom": "GB", "great britain": "GB", "grossbritannien": "GB", "großbritannien": "GB", "vereinigtes königreich": "GB", "vereinigtes koenigreich": "GB", "england": "GB", "gbr": "GB",
    "fr": "FR", "frankreich": "FR", "france": "FR", "fra": "FR",
    "it": "IT", "italien": "IT", "italy": "IT", "ita": "IT",
    "es": "ES", "spanien": "ES", "spain": "ES", "esp": "ES",
    "pt": "PT", "portugal": "PT", "prt": "PT",
    "nl": "NL", "niederlande": "NL", "netherlands": "NL", "holland": "NL", "nld": "NL",
    "be": "BE", "belgien": "BE", "belgium": "BE", "bel": "BE",
    "lu": "LU", "luxemburg": "LU", "luxembourg": "LU", "lux": "LU",
    "pl": "PL", "polen": "PL", "poland": "PL", "pol": "PL",
    "cz": "CZ", "tschechien": "CZ", "czech republic": "CZ", "czechia": "CZ", "cze": "CZ",
    "sk": "SK", "slowakei": "SK", "slovakia": "SK", "svk": "SK",
    "hu": "HU", "ungarn": "HU", "hungary": "HU", "hun": "HU",
    "dk": "DK", "dänemark": "DK", "daenemark": "DK", "denmark": "DK", "dnk": "DK",
    "se": "SE", "schweden": "SE", "sweden": "SE", "swe": "SE",
    "no": "NO", "norwegen": "NO", "norway": "NO", "nor": "NO",
    "fi": "FI", "finnland": "FI", "finland": "FI", "fin": "FI",
    "ie": "IE", "irland": "IE", "ireland": "IE", "irl": "IE",
    "gr": "GR", "griechenland": "GR", "greece": "GR", "grc": "GR",
    "ru": "RU", "russland": "RU", "russia": "RU", "russian federation": "RU", "rus": "RU",
    "ua": "UA", "ukraine": "UA", "ukr": "UA",
    "tr": "TR", "türkei": "TR", "tuerkei": "TR", "turkey": "TR", "tur": "TR",
    "cn": "CN", "china": "CN", "chn": "CN",
    "jp": "JP", "japan": "JP", "jpn": "JP",
    "kr": "KR", "südkorea": "KR", "suedkorea": "KR", "south korea": "KR", "korea": "KR", "kor": "KR",
    "in": "IN", "indien": "IN", "india": "IN", "ind": "IN",
    "au": "AU", "australien": "AU", "australia": "AU", "aus": "AU",
    "nz": "NZ", "neuseeland": "NZ", "new zealand": "NZ", "nzl": "NZ",
    "ca": "CA", "kanada": "CA", "canada": "CA", "can": "CA",
    "mx": "MX", "mexiko": "MX", "mexico": "MX", "mex": "MX",
    "br": "BR", "brasilien": "BR", "brazil": "BR", "bra": "BR",
    "ar": "AR", "argentinien": "AR", "argentina": AR if False else "AR", "arg": "AR",
    "za": "ZA", "südafrika": "ZA", "suedafrika": "ZA", "south africa": "ZA", "zaf": "ZA",
    "eg": "EG", "ägypten": "EG", "aegypten": "EG", "egypt": "EG", "egy": "EG",
    "ch.": "CH",
    "ch/che": "CH",
    "svizzera/schweiz": "CH",
    "ch (schweiz)": "CH",
    "de (deutschland)": "DE",
    "bundesrepublik deutschland": "DE",
    "brd": "DE",
    "swiss": "CH",
    "britain": "GB",
    "united-kingdom": "GB",
    "u.k.": "GB",
    "u.s.": "US",
    "u.s.a.": "US",
    "america": "US",
    "portugiesische republik": "PT",
    "hellas": "GR",
    "china prc": "CN",
    "prc": "CN",
    "peoples republic of china": "CN",
    "people's republic of china": "CN",
    "roc": "TW",
    "taiwan": "TW",
    "tw": "TW",
    "belgique": "BE",
    "españa": "ES",
    "italia": "IT",
    "deutschld": "DE",
}

def normalize_country(val):
    if pd.isna(val):
        return "UNKNOWN"
    s = str(val).strip().lower()
    s = s.replace(".", "").strip()
    if s == "":
        return "UNKNOWN"
    if s in country_map:
        return country_map[s]
    # try uppercase 2-letter code directly
    upper = str(val).strip().upper()
    if len(upper) == 2 and upper.isalpha():
        # check if it's a valid known code either via mapping values or as-is
        return upper
    return "UNKNOWN"

df["country"] = df["country"].apply(normalize_country)

df.to_parquet(output_path, index=False)