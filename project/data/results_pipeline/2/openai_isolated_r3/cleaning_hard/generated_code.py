import os
import re
import unicodedata
import pandas as pd
import numpy as np

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_isolated_r3/cleaning_hard/output.parquet"

country_aliases = {
    "AF": "af afghanistan afghan",
    "AL": "al albania albanien shqiperia",
    "DZ": "dz algeria algerien",
    "AD": "ad andorra",
    "AO": "ao angola",
    "AG": "ag antigua and barbuda antigua barbuda",
    "AR": "ar argentina argentinien",
    "AM": "am armenia armenien",
    "AU": "au australia australien commonwealth of australia",
    "AT": "at austria osterreich österreich republik osterreich republik österreich",
    "AZ": "az azerbaijan aserbaidschan azerbaidschan",
    "BS": "bs bahamas the bahamas",
    "BH": "bh bahrain bahrain",
    "BD": "bd bangladesh bangladesch",
    "BB": "bb barbados",
    "BY": "by belarus weissrussland weißrussland belorussia",
    "BE": "be belgium belgien",
    "BZ": "bz belize",
    "BJ": "bj benin bénin",
    "BT": "bt bhutan bhutan",
    "BO": "bo bolivia bolivien plurinational state of bolivia",
    "BA": "ba bosnia and herzegovina bosnien und herzegowina bosnia herzegovina",
    "BW": "bw botswana",
    "BR": "br brazil brasilien brasil",
    "BN": "bn brunei brunei darussalam",
    "BG": "bg bulgaria bulgarien",
    "BF": "bf burkina faso",
    "BI": "bi burundi",
    "CV": "cv cape verde cabo verde kap verde",
    "KH": "kh cambodia kambodscha",
    "CM": "cm cameroon kamerun",
    "CA": "ca canada kanada",
    "CF": "cf central african republic zentralafrikanische republik",
    "TD": "td chad tschad",
    "CL": "cl chile chili",
    "CN": "cn china peoples republic of china china prc volksrepublik china",
    "CO": "co colombia kolumbien",
    "KM": "km comoros komoren",
    "CG": "cg republic of the congo congo brazzaville republik kongo",
    "CD": "cd democratic republic of the congo dr congo congo kinshasa democratic republic congo demokratische republik kongo d r kongo",
    "CR": "cr costa rica kostarika",
    "CI": "ci cote d ivoire côte d ivoire ivory coast elfenbeinkuste elfenbeinküste",
    "HR": "hr croatia kroatien",
    "CU": "cu cuba kuba",
    "CY": "cy cyprus zypern",
    "CZ": "cz czechia czech republic tschechien tschechische republik",
    "DK": "dk denmark danemark dänemark",
    "DJ": "dj djibouti dschibuti",
    "DM": "dm dominica",
    "DO": "do dominican republic dominikanische republik",
    "EC": "ec ecuador equador",
    "EG": "eg egypt agypten ägypten",
    "SV": "sv el salvador",
    "GQ": "gq equatorial guinea aquatorialguinea äquatorialguinea",
    "ER": "er eritrea",
    "EE": "ee estonia estland",
    "SZ": "sz eswatini swaziland",
    "ET": "et ethiopia athiopien äthiopien",
    "FJ": "fj fiji fidschi",
    "FI": "fi finland finnland",
    "FR": "fr france frankreich french republic",
    "GA": "ga gabon",
    "GM": "gm gambia the gambia",
    "GE": "ge georgia georgien",
    "DE": "de deu ger germany deutschland german bundesrepublik deutschland federal republic of germany",
    "GH": "gh ghana",
    "GR": "gr greece griechenland hellas",
    "GD": "gd grenada",
    "GT": "gt guatemala",
    "GN": "gn guinea guinee",
    "GW": "gw guinea bissau guinea-bissau guineabissau",
    "GY": "gy guyana",
    "HT": "ht haiti haiti",
    "HN": "hn honduras",
    "HU": "hu hungary ungarn",
    "IS": "is iceland island",
    "IN": "in india indien bharat",
    "ID": "id indonesia indonesien",
    "IR": "ir iran islamic republic of iran iran iran",
    "IQ": "iq iraq irak",
    "IE": "ie ireland irland republic of ireland",
    "IL": "il israel",
    "IT": "it italy italien",
    "JM": "jm jamaica jamaika",
    "JP": "jp jpn japan japan nippon",
    "JO": "jo jordan jordanien",
    "KZ": "kz kazakhstan kasachstan",
    "KE": "ke kenya kenia",
    "KI": "ki kiribati",
    "KP": "kp north korea democratic peoples republic of korea nordkorea nord korea dprk",
    "KR": "kr south korea republic of korea sudkorea südkorea south korea rok",
    "KW": "kw kuwait kuwait",
    "KG": "kg kyrgyzstan kirgisistan kirgistan",
    "LA": "la laos lao peoples democratic republic laotische volksdemokratische republik",
    "LV": "lv latvia lettland",
    "LB": "lb lebanon libanon",
    "LS": "ls lesotho",
    "LR": "lr liberia liberia",
    "LY": "ly libya libyen",
    "LI": "li liechtenstein",
    "LT": "lt lithuania litauen",
    "LU": "lu luxembourg luxemburg",
    "MG": "mg madagascar madagaskar",
    "MW": "mw malawi malawi",
    "MY": "my malaysia malaysien",
    "MV": "mv maldives malediven",
    "ML": "ml mali",
    "MT": "mt malta",
    "MH": "mh marshall islands marshallinseln",
    "MR": "mr mauritania mauretanien",
    "MU": "mu mauritius mauritius",
    "MX": "mx mexico mexiko",
    "FM": "fm micronesia federated states of micronesia mikronesien",
    "MD": "md moldova moldau republic of moldova",
    "MC": "mc monaco monako",
    "MN": "mn mongolia mongolei",
    "ME": "me montenegro",
    "MA": "ma morocco marokko",
    "MZ": "mz mozambique mosambik mosambik",
    "MM": "mm myanmar burma birma",
    "NA": "na namibia namibia",
    "NR": "nr nauru",
    "NP": "np nepal nepál",
    "NL": "nl netherlands nederland niederlande holland",
    "NZ": "nz new zealand neuseeland",
    "NI": "ni nicaragua",
    "NE": "ne niger",
    "NG": "ng nigeria",
    "MK": "mk north macedonia macedonia nordmazedonien nord mazedonien mazedonien",
    "NO": "no norway norwegen",
    "OM": "om oman",
    "PK": "pk pakistan",
    "PW": "pw palau",
    "PS": "ps palestine state of palestine palestinian territories palastina palästina",
    "PA": "pa panama panamá",
    "PG": "pg papua new guinea papua neuguinea",
    "PY": "py paraguay",
    "PE": "pe peru perú",
    "PH": "ph philippines philippinen",
    "PL": "pl poland polen",
    "PT": "pt portugal",
    "QA": "qa qatar katar",
    "RO": "ro romania rumania rumänien",
    "RU": "ru rus russia russian federation russland russische foderation russische föderation",
    "RW": "rw rwanda ruanda",
    "KN": "kn saint kitts and nevis st kitts and nevis st kitts nevis",
    "LC": "lc saint lucia st lucia",
    "VC": "vc saint vincent and the grenadines st vincent and the grenadines st vincent grenadines",
    "WS": "ws samoa",
    "SM": "sm san marino",
    "ST": "st sao tome and principe sao tome principe são tomé and príncipe",
    "SA": "sa saudi arabia saudi arabien",
    "SN": "sn senegal",
    "RS": "rs serbia serbien",
    "SC": "sc seychelles seychellen",
    "SL": "sl sierra leone",
    "SG": "sg singapore singapur",
    "SK": "sk slovakia slowakei slowakische republik",
    "SI": "si slovenia slowenien",
    "SB": "sb solomon islands salomonen",
    "SO": "so somalia somalia",
    "ZA": "za south africa republic of south africa sudafrika südafrika rsa",
    "SS": "ss south sudan sudsudan süd sudan",
    "ES": "es esp spain spanien espana españa",
    "LK": "lk sri lanka",
    "SD": "sd sudan",
    "SR": "sr suriname surinam",
    "SE": "se sweden schweden sverige",
    "CH": "ch che switzerland schweiz suisse svizzera",
    "SY": "sy syria syrian arab republic syrien",
    "TW": "tw taiwan taiwan province of china republic of china",
    "TJ": "tj tajikistan tadschikistan",
    "TZ": "tz tanzania united republic of tanzania tansania",
    "TH": "th thailand thailand",
    "TL": "tl timor leste east timor osttimor",
    "TG": "tg togo",
    "TO": "to tonga",
    "TT": "tt trinidad and tobago trinidad tobago",
    "TN": "tn tunisia tunesien",
    "TR": "tr tur turkey turkiye türkiye turkey turkei türkei",
    "TM": "tm turkmenistan turkmenistan",
    "TV": "tv tuvalu",
    "UG": "ug uganda",
    "UA": "ua ukraine ukraine",
    "AE": "ae united arab emirates uae vereinigte arabische emirate v a e",
    "GB": "gb gbr uk united kingdom great britain britain england scotland wales northern ireland grossbritannien großbritannien vereinigtes konigreich vereinigtes königreich",
    "US": "us usa united states united states of america america vereinigte staaten vereinigte staaten von amerika",
    "UY": "uy uruguay",
    "UZ": "uz uzbekistan usbekistan",
    "VU": "vu vanuatu",
    "VA": "va vatican vatican city holy see vatikan vatikanstadt",
    "VE": "ve venezuela bolivarian republic of venezuela",
    "VN": "vn vietnam viet nam",
    "YE": "ye yemen jemen",
    "ZM": "zm zambia sambia",
    "ZW": "zw zimbabwe simbabue",
    "XK": "xk kosovo",
}

def normalize_text(value):
    if pd.isna(value):
        return ""
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()

lookup = {}
for iso_code, aliases in country_aliases.items():
    for alias in aliases.split("|"):
        normalized = normalize_text(alias)
        if normalized:
            lookup[normalized] = iso_code

for iso_code, aliases in country_aliases.items():
    for alias in aliases.split():
        normalized = normalize_text(alias)
        if len(normalized) >= 2:
            lookup.setdefault(normalized, iso_code)

def map_country(value):
    normalized = normalize_text(value)
    if not normalized:
        return "UNKNOWN"
    if normalized in lookup:
        return lookup[normalized]
    compact = normalized.replace(" ", "")
    if compact in lookup:
        return lookup[compact]
    return "UNKNOWN"

df = pd.read_parquet(input_path)
df["country"] = df["country"].map(map_country).astype("string")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)