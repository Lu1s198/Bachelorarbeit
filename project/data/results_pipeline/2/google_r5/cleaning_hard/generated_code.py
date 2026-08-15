import os
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r5/cleaning_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r5/cleaning_hard/output.parquet"

df = pd.read_parquet(input_path)

country_map = {
    # Germany
    "de": "DE",
    "deu": "DE",
    "ger": "DE",
    "germany": "DE",
    "deutschland": "DE",
    "bundesrepublik deutschland": "DE",
    "federal republic of germany": "DE",
    # Austria
    "at": "AT",
    "aut": "AT",
    "austria": "AT",
    "österreich": "AT",
    "oesterreich": "AT",
    # Switzerland
    "ch": "CH",
    "che": "CH",
    "switzerland": "CH",
    "schweiz": "CH",
    "suisse": "CH",
    "svizzera": "CH",
    # USA
    "us": "US",
    "usa": "US",
    "united states": "US",
    "united states of america": "US",
    "vereinigte staaten": "US",
    "vereinigte staaten von amerika": "US",
    # UK
    "gb": "GB",
    "gbr": "GB",
    "uk": "GB",
    "united kingdom": "GB",
    "great britain": "GB",
    "großbritannien": "GB",
    "grossbritannien": "GB",
    "vereinigtes königreich": "GB",
    "vereinigtes koenigreich": "GB",
    "england": "GB",
    # France
    "fr": "FR",
    "fra": "FR",
    "france": "FR",
    "frankreich": "FR",
    # Italy
    "it": "IT",
    "ita": "IT",
    "italy": "IT",
    "italien": "IT",
    # Spain
    "es": "ES",
    "esp": "ES",
    "spain": "ES",
    "spanien": "ES",
    # Netherlands
    "nl": "NL",
    "nld": "NL",
    "netherlands": "NL",
    "niederlande": "NL",
    "holland": "NL",
    # Belgium
    "be": "BE",
    "bel": "BE",
    "belgium": "BE",
    "belgien": "BE",
    # Poland
    "pl": "PL",
    "pol": "PL",
    "poland": "PL",
    "polen": "PL",
    # Czech Republic
    "cz": "CZ",
    "cze": "CZ",
    "czech republic": "CZ",
    "czechia": "CZ",
    "tschechien": "CZ",
    "tschechische republik": "CZ",
    # Denmark
    "dk": "DK",
    "dnk": "DK",
    "denmark": "DK",
    "dänemark": "DK",
    "daenemark": "DK",
    # Sweden
    "se": "SE",
    "swe": "SE",
    "sweden": "SE",
    "schweden": "SE",
    # Norway
    "no": "NO",
    "nor": "NO",
    "norway": "NO",
    "norwegen": "NO",
    # Finland
    "fi": "FI",
    "fin": "FI",
    "finland": "FI",
    "finnland": "FI",
    # Ireland
    "ie": "IE",
    "irl": "IE",
    "ireland": "IE",
    "irland": "IE",
    # Portugal
    "pt": "PT",
    "prt": "PT",
    "portugal": "PT",
    # Luxembourg
    "lu": "LU",
    "lux": "LU",
    "luxembourg": "LU",
    "luxemburg": "LU",
    # Liechtenstein
    "li": "LI",
    "lie": "LI",
    "liechtenstein": "LI",
    # Canada
    "ca": "CA",
    "can": "CA",
    "canada": "CA",
    "kanada": "CA",
    # Australia
    "au": "AU",
    "aus": "AU",
    "australia": "AU",
    "australien": "AU",
    # New Zealand
    "nz": "NZ",
    "nzl": "NZ",
    "new zealand": "NZ",
    "neuseeland": "NZ",
    # China
    "cn": "CN",
    "chn": "CN",
    "china": "CN",
    # Japan
    "jp": "JP",
    "jpn": "JP",
    "japan": "JP",
    # India
    "in": "IN",
    "ind": "IN",
    "india": "IN",
    "indien": "IN",
    # Brazil
    "br": "BR",
    "bra": "BR",
    "brazil": "BR",
    "brasilien": "BR",
    # Russia
    "ru": "RU",
    "rus": "RU",
    "russia": "RU",
    "russland": "RU",
    # Turkey
    "tr": "TR",
    "tur": "TR",
    "turkey": "TR",
    "türkei": "TR",
    "tuerkei": "TR",
    # Greece
    "gr": "GR",
    "grc": "GR",
    "greece": "GR",
    "griechenland": "GR",
    # Mexico
    "mx": "MX",
    "mex": "MX",
    "mexico": "MX",
    "mexiko": "MX",
    # South Africa
    "za": "ZA",
    "zaf": "ZA",
    "south africa": "ZA",
    "südafrika": "ZA",
    "suedafrika": "ZA",
    # Hungary
    "hu": "HU",
    "hun": "HU",
    "hungary": "HU",
    "ungarn": "HU",
    # Romania
    "ro": "RO",
    "rou": "RO",
    "romania": "RO",
    "rumänien": "RO",
    "rumaenien": "RO",
    # Slovakia
    "sk": "SK",
    "svk": "SK",
    "slovakia": "SK",
    "slowakei": "SK",
    # Slovenia
    "si": "SI",
    "svn": "SI",
    "slovenia": "SI",
    "slowenien": "SI",
    # Croatia
    "hr": "HR",
    "hrv": "HR",
    "croatia": "HR",
    "kroatien": "HR",
    # Bulgaria
    "bg": "BG",
    "bgr": "BG",
    "bulgaria": "BG",
    "bulgarien": "BG",
    # Ukraine
    "ua": "UA",
    "ukr": "UA",
    "ukraine": "UA",
}


def map_country(val):
    if pd.isna(val):
        return "UNKNOWN"
    s = str(val).strip().lower()
    return country_map.get(s, "UNKNOWN")


df["country"] = df["country"].apply(map_country)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)