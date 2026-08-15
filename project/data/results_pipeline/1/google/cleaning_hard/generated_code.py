import os
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/cleaning_medium/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/cleaning_hard/output.parquet"

df = pd.read_parquet(input_path)

country_mapping = {
    # Germany
    "de": "DE", "deu": "DE", "ger": "DE", "deutschland": "DE", "germany": "DE", "d": "DE",
    # Austria
    "at": "AT", "aut": "AT", "österreich": "AT", "oesterreich": "AT", "austria": "AT",
    # Switzerland
    "ch": "CH", "che": "CH", "sui": "CH", "schweiz": "CH", "switzerland": "CH",
    # United States
    "us": "US", "usa": "US", "united states": "US", "united states of america": "US",
    "vereinigte staaten": "US", "vereinigte staaten von amerika": "US", "us of a": "US",
    # United Kingdom
    "gb": "GB", "gbr": "GB", "uk": "GB", "united kingdom": "GB", "great britain": "GB",
    "großbritannien": "GB", "grossbritannien": "GB", "england": "GB", "eng": "GB",
    # France
    "fr": "FR", "fra": "FR", "france": "FR", "frankreich": "FR",
    # Italy
    "it": "IT", "ita": "IT", "italy": "IT", "italien": "IT",
    # Spain
    "es": "ES", "esp": "ES", "spain": "ES", "spanien": "ES",
    # Netherlands
    "nl": "NL", "nld": "NL", "ned": "NL", "netherlands": "NL", "niederlande": "NL", "holland": "NL",
    # Belgium
    "be": "BE", "bel": "BE", "belgium": "BE", "belgien": "BE",
    # Poland
    "pl": "PL", "pol": "PL", "poland": "PL", "polen": "PL",
    # Canada
    "ca": "CA", "can": "CA", "canada": "CA", "kanada": "CA",
    # Australia
    "au": "AU", "aus": "AU", "australia": "AU", "australien": "AU",
    # China
    "cn": "CN", "chn": "CN", "china": "CN",
    # Japan
    "jp": "JP", "jpn": "JP", "japan": "JP",
    # India
    "in": "IN", "ind": "IN", "india": "IN", "indien": "IN",
    # Brazil
    "br": "BR", "bra": "BR", "brazil": "BR", "brasilien": "BR",
    # Russia
    "ru": "RU", "rus": "RU", "russia": "RU", "russland": "RU",
    # Sweden
    "se": "SE", "swe": "SE", "sweden": "SE", "schweden": "SE",
    # Norway
    "no": "NO", "nor": "NO", "norway": "NO", "norwegen": "NO",
    # Denmark
    "dk": "DK", "dnk": "DK", "den": "DK", "denmark": "DK", "dänemark": "DK", "daenemark": "DK",
    # Finland
    "fi": "FI", "fin": "FI", "finland": "FI", "finnland": "FI",
    # Portugal
    "pt": "PT", "prt": "PT", "por": "PT", "portugal": "PT",
    # Ireland
    "ie": "IE", "irl": "IE", "ireland": "IE", "irland": "IE",
    # Czech Republic
    "cz": "CZ", "cze": "CZ", "czech republic": "CZ", "czechia": "CZ", "tschechien": "CZ",
    # Hungary
    "hu": "HU", "hun": "HU", "hungary": "HU", "ungarn": "HU",
    # Romania
    "ro": "RO", "rou": "RO", "rom": "RO", "romania": "RO", "rumänien": "RO", "rumaenien": "RO",
    # Turkey
    "tr": "TR", "tur": "TR", "turkey": "TR", "türkei": "TR", "tuerkei": "TR", "türkiye": "TR",
    # Greece
    "gr": "GR", "grc": "GR", "gre": "GR", "greece": "GR", "griechenland": "GR",
    # Mexico
    "mx": "MX", "mex": "MX", "mexico": "MX", "mexiko": "MX",
    # South Africa
    "za": "ZA", "zaf": "ZA", "rsa": "ZA", "south africa": "ZA", "südafrika": "ZA", "suedafrika": "ZA",
    # New Zealand
    "nz": "NZ", "nzl": "NZ", "new zealand": "NZ", "neuseeland": "NZ",
    # Singapore
    "sg": "SG", "sgp": "SG", "singapore": "SG", "singapur": "SG",
    # Hong Kong
    "hk": "HK", "hkg": "HK", "hong kong": "HK", "hongkong": "HK",
    # South Korea
    "kr": "KR", "kor": "KR", "south korea": "KR", "südkorea": "KR", "suedkorea": "KR", "korea": "KR",
    # Argentina
    "ar": "AR", "arg": "AR", "argentina": "AR", "argentinien": "AR",
    # Chile
    "cl": "CL", "chl": "CL", "chile": "CL",
    # Colombia
    "co": "CO", "col": "CO", "colombia": "CO", "kolumbien": "CO",
    # Egypt
    "eg": "EG", "egy": "EG", "egypt": "EG", "ägypten": "EG", "aegypten": "EG",
    # Ukraine
    "ua": "UA", "ukr": "UA", "ukraine": "UA",
    # Israel
    "il": "IL", "isr": "IL", "israel": "IL",
    # UAE
    "ae": "AE", "uae": "AE", "united arab emirates": "AE", "vae": "AE", "vereinigte arabische emirate": "AE",
    # Thailand
    "th": "TH", "tha": "TH", "thailand": "TH",
    # Vietnam
    "vn": "VN", "vnm": "VN", "vietnam": "VN",
    # Indonesia
    "id": "ID", "idn": "ID", "indonesia": "ID", "indonesien": "ID",
    # Malaysia
    "my": "MY", "mys": "MY", "malaysia": "MY",
    # Philippines
    "ph": "PH", "phl": "PH", "philippines": "PH", "philippinen": "PH",
    # Pakistan
    "pk": "PK", "pak": "PK", "pakistan": "PK",
    # Bangladesh
    "bd": "BD", "bgd": "BD", "bangladesh": "BD", "bangladesch": "BD",
    # Nigeria
    "ng": "NG", "nga": "NG", "nigeria": "NG",
    # Kenya
    "ke": "KE", "ken": "KE", "kenya": "KE", "kenia": "KE",
    # Luxembourg
    "lu": "LU", "lux": "LU", "luxembourg": "LU", "luxemburg": "LU",
    # Liechtenstein
    "li": "LI", "lie": "LI", "liechtenstein": "LI",
    # Slovakia
    "sk": "SK", "svk": "SK", "slovakia": "SK", "slowakei": "SK",
    # Slovenia
    "si": "SI", "svn": "SI", "slovenia": "SI", "slowenien": "SI",
    # Croatia
    "hr": "HR", "hrv": "HR", "croatia": "HR", "kroatien": "HR",
    # Bulgaria
    "bg": "BG", "bgr": "BG", "bulgaria": "BG", "bulgarien": "BG",
    # Estonia
    "ee": "EE", "est": "EE", "estonia": "EE", "estland": "EE",
    # Latvia
    "lv": "LV", "lva": "LV", "latvia": "LV", "lettland": "LV",
    # Lithuania
    "lt": "LT", "ltu": "LT", "lithuania": "LT", "litauen": "LT",
    # Iceland
    "is": "IS", "isl": "IS", "iceland": "IS", "island": "IS",
    # Malta
    "mt": "MT", "mlt": "MT", "malta": "MT",
    # Cyprus
    "cy": "CY", "cyp": "CY", "cyprus": "CY", "zypern": "CY"
}

def clean_country(val):
    if pd.isna(val) or not isinstance(val, str):
        return "UNKNOWN"
    val_str = val.strip().lower()
    return country_mapping.get(val_str, "UNKNOWN")

df["country"] = df["country"].apply(clean_country)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)