import pandas as pd
import numpy as np

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r4/cleaning_medium/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r4/cleaning_hard/output.parquet"

df = pd.read_parquet(input_path)

country_map = {
    # Germany
    "germany": "DE", "deutschland": "DE", "de": "DE", "deu": "DE", "ger": "DE",
    "d": "DE", "bundesrepublik deutschland": "DE",
    # Austria
    "austria": "AT", "oesterreich": "AT", "österreich": "AT", "at": "AT", "aut": "AT",
    # Switzerland
    "switzerland": "CH", "schweiz": "CH", "suisse": "CH", "ch": "CH", "che": "CH",
    "swiss": "CH", "confoederatio helvetica": "CH",
    # France
    "france": "FR", "frankreich": "FR", "fr": "FR", "fra": "FR",
    # United Kingdom
    "united kingdom": "GB", "grossbritannien": "GB", "großbritannien": "GB",
    "great britain": "GB", "uk": "GB", "gb": "GB", "gbr": "GB", "england": "GB",
    "vereinigtes koenigreich": "GB", "vereinigtes königreich": "GB",
    # United States
    "united states": "US", "united states of america": "US", "usa": "US",
    "us": "US", "vereinigte staaten": "US", "vereinigte staaten von amerika": "US",
    "amerika": "US", "u.s.a.": "US", "u.s.": "US",
    # Netherlands
    "netherlands": "NL", "niederlande": "NL", "nl": "NL", "nld": "NL", "holland": "NL",
    # Belgium
    "belgium": "BE", "belgien": "BE", "be": "BE", "bel": "BE",
    # Spain
    "spain": "ES", "spanien": "ES", "es": "ES", "esp": "ES",
    # Italy
    "italy": "IT", "italien": "IT", "it": "IT", "ita": "IT",
    # Poland
    "poland": "PL", "polen": "PL", "pl": "PL", "pol": "PL",
    # Portugal
    "portugal": "PT", "pt": "PT", "prt": "PT",
    # Sweden
    "sweden": "SE", "schweden": "SE", "se": "SE", "swe": "SE",
    # Norway
    "norway": "NO", "norwegen": "NO", "no": "NO", "nor": "NO",
    # Denmark
    "denmark": "DK", "daenemark": "DK", "dänemark": "DK", "dk": "DK", "dnk": "DK",
    # Finland
    "finland": "FI", "finnland": "FI", "fi": "FI", "fin": "FI",
    # Ireland
    "ireland": "IE", "irland": "IE", "ie": "IE", "irl": "IE",
    # Luxembourg
    "luxembourg": "LU", "luxemburg": "LU", "lu": "LU", "lux": "LU",
    # Greece
    "greece": "GR", "griechenland": "GR", "gr": "GR", "grc": "GR",
    # Czech Republic
    "czech republic": "CZ", "tschechien": "CZ", "cz": "CZ", "cze": "CZ",
    "czechia": "CZ",
    # Slovakia
    "slovakia": "SK", "slowakei": "SK", "sk": "SK", "svk": "SK",
    # Hungary
    "hungary": "HU", "ungarn": "HU", "hu": "HU", "hun": "HU",
    # Romania
    "romania": "RO", "rumaenien": "RO", "rumänien": "RO", "ro": "RO", "rou": "RO",
    # Bulgaria
    "bulgaria": "BG", "bulgarien": "BG", "bg": "BG", "bgr": "BG",
    # Croatia
    "croatia": "HR", "kroatien": "HR", "hr": "HR", "hrv": "HR",
    # Slovenia
    "slovenia": "SI", "slowenien": "SI", "si": "SI", "svn": "SI",
    # Estonia
    "estonia": "EE", "estland": "EE", "ee": "EE", "est": "EE",
    # Latvia
    "latvia": "LV", "lettland": "LV", "lv": "LV", "lva": "LV",
    # Lithuania
    "lithuania": "LT", "litauen": "LT", "lt": "LT", "ltu": "LT",
    # Iceland
    "iceland": "IS", "island": "IS", "is": "IS", "isl": "IS",
    # Malta
    "malta": "MT", "mt": "MT", "mlt": "MT",
    # Cyprus
    "cyprus": "CY", "zypern": "CY", "cy": "CY", "cyp": "CY",
    # Russia
    "russia": "RU", "russland": "RU", "ru": "RU", "rus": "RU",
    "russian federation": "RU",
    # Ukraine
    "ukraine": "UA", "ua": "UA", "ukr": "UA",
    # Turkey
    "turkey": "TR", "tuerkei": "TR", "türkei": "TR", "tr": "TR", "tur": "TR",
    # China
    "china": "CN", "cn": "CN", "chn": "CN",
    # Japan
    "japan": "JP", "jp": "JP", "jpn": "JP",
    # South Korea
    "south korea": "KR", "suedkorea": "KR", "südkorea": "KR", "kr": "KR", "kor": "KR",
    # India
    "india": "IN", "indien": "IN", "in": "IN", "ind": "IN",
    # Canada
    "canada": "CA", "kanada": "CA", "ca": "CA", "can": "CA",
    # Australia
    "australia": "AU", "australien": "AU", "au": "AU", "aus": "AU",
    # New Zealand
    "new zealand": "NZ", "neuseeland": "NZ", "nz": "NZ", "nzl": "NZ",
    # Brazil
    "brazil": "BR", "brasilien": "BR", "br": "BR", "bra": "BR",
    # Argentina
    "argentina": "AR", "argentinien": "AR", "ar": "AR", "arg": "AR",
    # Mexico
    "mexico": "MX", "mexiko": "MX", "mx": "MX", "mex": "MX",
    # South Africa
    "south africa": "ZA", "suedafrika": "ZA", "südafrika": "ZA", "za": "ZA", "zaf": "ZA",
    # Egypt
    "egypt": "EG", "aegypten": "EG", "ägypten": "EG", "eg": "EG", "egy": "EG",
    # Israel
    "israel": "IL", "il": "IL", "isr": "IL",
    # Saudi Arabia
    "saudi arabia": "SA", "saudi-arabien": "SA", "sa": "SA", "sau": "SA",
    # United Arab Emirates
    "united arab emirates": "AE", "vereinigte arabische emirate": "AE", "ae": "AE",
    "are": "AE", "uae": "AE",
    # Thailand
    "thailand": "TH", "th": "TH", "tha": "TH",
    # Indonesia
    "indonesia": "ID", "indonesien": "ID", "id": "ID", "idn": "ID",
    # Vietnam
    "vietnam": "VN", "vn": "VN", "vnm": "VN",
    # Philippines
    "philippines": "PH", "philippinen": "PH", "ph": "PH", "phl": "PH",
    # Malaysia
    "malaysia": "MY", "my": "MY", "mys": "MY",
    # Singapore
    "singapore": "SG", "singapur": "SG", "sg": "SG", "sgp": "SG",
    # Pakistan
    "pakistan": "PK", "pk": "PK", "pak": "PK",
    # Bangladesh
    "bangladesh": "BD", "bd": "BD", "bgd": "BD",
    # Chile
    "chile": "CL", "cl": "CL", "chl": "CL",
    # Colombia
    "colombia": "CO", "kolumbien": "CO", "co": "CO", "col": "CO",
    # Peru
    "peru": "PE", "pe": "PE", "per": "PE",
    # Venezuela
    "venezuela": "VE", "ve": "VE", "ven": "VE",
    # Serbia
    "serbia": "RS", "serbien": "RS", "rs": "RS", "srb": "RS",
    # Bosnia
    "bosnia and herzegovina": "BA", "bosnien": "BA", "ba": "BA", "bih": "BA",
    # Albania
    "albania": "AL", "albanien": "AL", "al": "AL", "alb": "AL",
    # Belarus
    "belarus": "BY", "weissrussland": "BY", "weißrussland": "BY", "by": "BY", "blr": "BY",
    # Moldova
    "moldova": "MD", "moldawien": "MD", "md": "MD", "mda": "MD",
    # Georgia
    "georgia": "GE", "georgien": "GE", "ge": "GE", "geo": "GE",
    # Armenia
    "armenia": "AM", "armenien": "AM", "am": "AM", "arm": "AM",
    # Azerbaijan
    "azerbaijan": "AZ", "aserbaidschan": "AZ", "az": "AZ", "aze": "AZ",
    # Kazakhstan
    "kazakhstan": "KZ", "kasachstan": "KZ", "kz": "KZ", "kaz": "KZ",
    # Iran
    "iran": "IR", "ir": "IR", "irn": "IR",
    # Iraq
    "iraq": "IQ", "irak": "IQ", "iq": "IQ", "irq": "IQ",
    # Nigeria
    "nigeria": "NG", "ng": "NG", "nga": "NG",
    # Kenya
    "kenya": "KE", "kenia": "KE", "ke": "KE", "ken": "KE",
    # Morocco
    "morocco": "MA", "marokko": "MA", "ma": "MA", "mar": "MA",
    # Algeria
    "algeria": "DZ", "algerien": "DZ", "dz": "DZ", "dza": "DZ",
    # Tunisia
    "tunisia": "TN", "tunesien": "TN", "tn": "TN", "tun": "TN",
}


def normalize_country(val):
    if pd.isna(val):
        return "UNKNOWN"
    s = str(val).strip().lower()
    s = s.replace(".", "").replace("_", " ").replace("-", " ")
    s = " ".join(s.split())
    if s == "":
        return "UNKNOWN"
    if s in country_map:
        return country_map[s]
    # try without spaces
    s_nospace = s.replace(" ", "")
    if s_nospace in country_map:
        return country_map[s_nospace]
    return "UNKNOWN"


df["country"] = df["country"].apply(normalize_country)

df.to_parquet(output_path, index=False)