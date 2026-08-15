import os
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_isolated_r4/cleaning_hard/output.parquet"

df = pd.read_parquet(input_path)

country_mapping = {
    # DE
    "de": "DE", "deu": "DE", "ger": "DE", "germany": "DE", "deutschland": "DE", "deutschland (bundesrepublik)": "DE", "brd": "DE",
    # AT
    "at": "AT", "aut": "AT", "austria": "AT", "österreich": "AT", "oesterreich": "AT",
    # CH
    "ch": "CH", "che": "CH", "switzerland": "CH", "schweiz": "CH", "suisse": "CH", "svizzera": "CH",
    # US
    "us": "US", "usa": "US", "united states": "US", "united states of america": "US", "vereinigte staaten": "US", "vereinigte staaten von amerika": "US",
    # GB
    "gb": "GB", "gbr": "GB", "uk": "GB", "united kingdom": "GB", "great britain": "GB", "vereinigtes königreich": "GB", "vereinigtes koenigreich": "GB", "england": "GB", "großbritannien": "GB", "grossbritannien": "GB",
    # FR
    "fr": "FR", "fra": "FR", "france": "FR", "frankreich": "FR",
    # IT
    "it": "IT", "ita": "IT", "italy": "IT", "italien": "IT",
    # ES
    "es": "ES", "esp": "ES", "spain": "ES", "spanien": "ES",
    # NL
    "nl": "NL", "nld": "NL", "netherlands": "NL", "niederlande": "NL", "holland": "NL",
    # BE
    "be": "BE", "bel": "BE", "belgium": "BE", "belgien": "BE",
    # PL
    "pl": "PL", "pol": "PL", "poland": "PL", "polen": "PL",
    # CZ
    "cz": "CZ", "cze": "CZ", "czech republic": "CZ", "czechia": "CZ", "tschechien": "CZ", "tschechische republik": "CZ",
    # DK
    "dk": "DK", "dnk": "DK", "denmark": "DK", "dänemark": "DK", "daenemark": "DK",
    # SE
    "se": "SE", "swe": "SE", "sweden": "SE", "schweden": "SE",
    # NO
    "no": "NO", "nor": "NO", "norway": "NO", "norwegen": "NO",
    # FI
    "fi": "FI", "fin": "FI", "finland": "FI", "finnland": "FI",
    # PT
    "pt": "PT", "prt": "PT", "portugal": "PT",
    # GR
    "gr": "GR", "grc": "GR", "greece": "GR", "griechenland": "GR",
    # TR
    "tr": "TR", "tur": "TR", "turkey": "TR", "türkei": "TR", "tuerkei": "TR", "türkiye": "TR",
    # RU
    "ru": "RU", "rus": "RU", "russia": "RU", "russland": "RU", "russian federation": "RU",
    # CN
    "cn": "CN", "chn": "CN", "china": "CN",
    # JP
    "jp": "JP", "jpn": "JP", "japan": "JP",
    # IN
    "in": "IN", "ind": "IN", "india": "IN", "indien": "IN",
    # BR
    "br": "BR", "bra": "BR", "brazil": "BR", "brasilien": "BR",
    # CA
    "ca": "CA", "can": "CA", "canada": "CA", "kanada": "CA",
    # AU
    "au": "AU", "aus": "AU", "australia": "AU", "australien": "AU",
    # ZA
    "za": "ZA", "zaf": "ZA", "south africa": "ZA", "südafrika": "ZA", "suedafrika": "ZA",
    # MX
    "mx": "MX", "mex": "MX", "mexico": "MX", "mexiko": "MX",
    # IE
    "ie": "IE", "irl": "IE", "ireland": "IE", "irland": "IE",
    # LU
    "lu": "LU", "lux": "LU", "luxembourg": "LU", "luxemburg": "LU",
    # LI
    "li": "LI", "lie": "LI", "liechtenstein": "LI",
    # HU
    "hu": "HU", "hun": "HU", "hungary": "HU", "ungarn": "HU",
    # RO
    "ro": "RO", "rou": "RO", "romania": "RO", "rumänien": "RO", "rumaenien": "RO",
    # BG
    "bg": "BG", "bgr": "BG", "bulgaria": "BG", "bulgarien": "BG",
    # HR
    "hr": "HR", "hrv": "HR", "croatia": "HR", "kroatien": "HR",
    # SK
    "sk": "SK", "svk": "SK", "slovakia": "SK", "slowakei": "SK",
    # SI
    "si": "SI", "svn": "SI", "slovenia": "SI", "slowenien": "SI",
    # UA
    "ua": "UA", "ukr": "UA", "ukraine": "UA",
    # EE / LV / LT
    "ee": "EE", "est": "EE", "estonia": "EE", "estland": "EE",
    "lv": "LV", "lva": "LV", "latvia": "LV", "lettland": "LV",
    "lt": "LT", "ltu": "LT", "lithuania": "LT", "litauen": "LT",
    # IS
    "is": "IS", "isl": "IS", "iceland": "IS", "island": "IS",
    # NZ
    "nz": "NZ", "nzl": "NZ", "new zealand": "NZ", "neuseeland": "NZ",
    # AR
    "ar": "AR", "arg": "AR", "argentina": "AR", "argentinien": "AR",
    # CL
    "cl": "CL", "chl": "CL", "chile": "CL",
    # CO
    "co": "CO", "col": "CO", "colombia": "CO", "kolumbien": "CO",
    # EG
    "eg": "EG", "egy": "EG", "egypt": "EG", "ägypten": "EG", "aegypten": "EG",
    # ID
    "id": "ID", "idn": "ID", "indonesia": "ID", "indonesien": "ID",
    # IL
    "il": "IL", "isr": "IL", "israel": "IL",
    # KR
    "kr": "KR", "kor": "KR", "south korea": "KR", "korea": "KR", "südkorea": "KR", "suedkorea": "KR",
    # MY
    "my": "MY", "mys": "MY", "malaysia": "MY",
    # PH
    "ph": "PH", "phl": "PH", "philippines": "PH", "philippinen": "PH",
    # SG
    "sg": "SG", "sgp": "SG", "singapore": "SG", "singapur": "SG", "singapore": "SG",
    # TH
    "th": "TH", "tha": "TH", "thailand": "TH",
    # VN
    "vn": "VN", "vnm": "VN", "vietnam": "VN",
    # SA
    "sa": "SA", "sau": "SA", "saudi arabia": "SA", "saudi-arabien": "SA",
    # AE
    "ae": "AE", "are": "AE", "uae": "AE", "united arab emirates": "AE", "vereinigte arabische emirate": "AE",
}

valid_iso_alpha2 = {
    "AD", "AE", "AF", "AG", "AI", "AL", "AM", "AO", "AQ", "AR", "AS", "AT", "AU", "AW", "AX", "AZ",
    "BA", "BB", "BD", "BE", "BF", "BG", "BH", "BI", "BJ", "BL", "BM", "BN", "BO", "BQ", "BR", "BS", "BT", "BV", "BW", "BY", "BZ",
    "CA", "CC", "CD", "CF", "CG", "CH", "CI", "CK", "CL", "CM", "CN", "CO", "CR", "CU", "CV", "CW", "CX", "CY", "CZ",
    "DE", "DJ", "DK", "DM", "DO", "DZ",
    "EC", "EE", "EG", "EH", "ER", "ES", "ET",
    "FI", "FJ", "FK", "FM", "FO", "FR",
    "GA", "GB", "GD", "GE", "GF", "GG", "GH", "GI", "GL", "GM", "GN", "GP", "GQ", "GR", "GS", "GT", "GU", "GW", "GY",
    "HK", "HM", "HN", "HR", "HT", "HU",
    "ID", "IE", "IL", "IM", "IN", "IO", "IQ", "IR", "IS", "IT",
    "JE", "JM", "JO", "JP",
    "KE", "KG", "KH", "KI", "KM", "KN", "KP", "KR", "KW", "KY", "KZ",
    "LA", "LB", "LC", "LI", "LK", "LR", "LS", "LT", "LU", "LV", "LY",
    "MA", "MC", "MD", "ME", "MF", "MG", "MH", "MK", "ML", "MM", "MN", "MO", "MP", "MQ", "MR", "MS", "MT", "MU", "MV", "MW", "MX", "MY", "MZ",
    "NA", "NC", "NE", "NF", "NG", "NI", "NL", "NO", "NP", "NR", "NU", "NZ",
    "OM",
    "PA", "PE", "PF", "PG", "PH", "PK", "PL", "PM", "PN", "PR", "PS", "PT", "PW", "PY",
    "QA",
    "RE", "RO", "RS", "RU", "RW",
    "SA", "SB", "SC", "SD", "SE", "SG", "SH", "SI", "SJ", "SK", "SL", "SM", "SN", "SO", "SR", "SS", "ST", "SV", "SX", "SY", "SZ",
    "TC", "TD", "TF", "TG", "TH", "TJ", "TK", "TL", "TM", "TN", "TO", "TR", "TT", "TV", "TW", "TZ",
    "UA", "UG", "UM", "US", "UY", "UZ",
    "VA", "VC", "VE", "VG", "VI", "VN", "VU",
    "WF", "WS",
    "YE", "YT",
    "ZA", "ZM", "ZW"
}

def clean_country(val):
    if pd.isna(val):
        return "UNKNOWN"
    s = str(val).strip()
    if not s:
        return "UNKNOWN"
    s_upper = s.upper()
    if s_upper in valid_iso_alpha2:
        return s_upper
    s_lower = s.lower()
    return country_mapping.get(s_lower, "UNKNOWN")

df['country'] = df['country'].apply(clean_country)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)