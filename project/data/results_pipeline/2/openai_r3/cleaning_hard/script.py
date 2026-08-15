import os
import re
import unicodedata
import pandas as pd
import numpy as np

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r3/cleaning_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r3/cleaning_hard/output.parquet"

def normalize_value(value):
    if pd.isna(value):
        return ""
    text = str(value).strip().casefold()
    text = text.replace("ß", "ss")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.replace("&", " and ")
    text = re.sub(r"[\.\,\;\:\'\"\(\)\[\]\{\}/\\_\-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

country_aliases = {
    "AF": ["af", "afg", "afghanistan"],
    "AL": ["al", "alb", "albania", "albanien"],
    "DZ": ["dz", "dza", "algeria", "algerien"],
    "AD": ["ad", "and", "andorra"],
    "AO": ["ao", "ago", "angola"],
    "AG": ["ag", "atg", "antigua and barbuda", "antigua und barbuda"],
    "AR": ["ar", "arg", "argentina", "argentinien"],
    "AM": ["am", "arm", "armenia", "armenien"],
    "AU": ["au", "aus", "australia", "australien"],
    "AT": ["at", "aut", "austria", "osterreich", "österreich"],
    "AZ": ["az", "aze", "azerbaijan", "azerbaidschan"],
    "BS": ["bs", "bhs", "bahamas", "the bahamas"],
    "BH": ["bh", "bhr", "bahrain", "bahrain"],
    "BD": ["bd", "bgd", "bangladesh", "bangladesch"],
    "BB": ["bb", "brb", "barbados"],
    "BY": ["by", "blr", "belarus", "belarus", "weissrussland", "weißrussland"],
    "BE": ["be", "bel", "belgium", "belgien"],
    "BZ": ["bz", "blz", "belize"],
    "BJ": ["bj", "ben", "benin"],
    "BT": ["bt", "btn", "bhutan", "bhutan"],
    "BO": ["bo", "bol", "bolivia", "bolivien", "plurinational state of bolivia"],
    "BA": ["ba", "bih", "bosnia and herzegovina", "bosnien und herzegowina", "bosnia herzegovina"],
    "BW": ["bw", "bwa", "botswana"],
    "BR": ["br", "bra", "brazil", "brasilien", "brasil"],
    "BN": ["bn", "brn", "brunei", "brunei darussalam"],
    "BG": ["bg", "bgr", "bulgaria", "bulgarien"],
    "BF": ["bf", "bfa", "burkina faso"],
    "BI": ["bi", "bdi", "burundi"],
    "CV": ["cv", "cpv", "cape verde", "cabo verde", "kap verde"],
    "KH": ["kh", "khm", "cambodia", "kambodscha"],
    "CM": ["cm", "cmr", "cameroon", "kamerun"],
    "CA": ["ca", "can", "canada", "kanada"],
    "CF": ["cf", "caf", "central african republic", "central african republic", "zentralafrikanische republik"],
    "TD": ["td", "tcd", "chad", "tschad"],
    "CL": ["cl", "chl", "chile"],
    "CN": ["cn", "chn", "china", "volksrepublik china", "people s republic of china", "pr china"],
    "CO": ["co", "col", "colombia", "kolumbien"],
    "KM": ["km", "com", "comoros", "komoren"],
    "CD": ["cd", "cod", "democratic republic of the congo", "democratic republic congo", "dr congo", "d r congo", "drc", "congo kinshasa", "demokratische republik kongo"],
    "CG": ["cg", "cog", "republic of the congo", "republic congo", "congo brazzaville", "republik kongo"],
    "CR": ["cr", "cri", "costa rica"],
    "CI": ["ci", "civ", "cote d ivoire", "cote divoire", "ivory coast", "elfenbeinkuste", "elfenbeinküste"],
    "HR": ["hr", "hrv", "croatia", "kroatien"],
    "CU": ["cu", "cub", "cuba", "kuba"],
    "CY": ["cy", "cyp", "cyprus", "zypern"],
    "CZ": ["cz", "cze", "czechia", "czech republic", "tschechien", "tschechische republik"],
    "DK": ["dk", "dnk", "denmark", "danemark"],
    "DJ": ["dj", "dji", "djibouti", "dschibuti"],
    "DM": ["dm", "dma", "dominica", "dominica"],
    "DO": ["do", "dom", "dominican republic", "dominikanische republik"],
    "EC": ["ec", "ecu", "ecuador", "ecuador"],
    "EG": ["eg", "egy", "egypt", "agypten", "ägypten"],
    "SV": ["sv", "slv", "el salvador"],
    "GQ": ["gq", "gnq", "equatorial guinea", "aquinatorial guinea", "aquatorial guinea", "aquatorialguinea", "aquatorial guinea", "aquatorialguinea", "aquatorial guinea", "aquatorialguinea", "aquatorial guinea", "aquatorialguinea", "aquatorial guinea", "aquatorialguinea", "aquatorial guinea", "aquatorialguinea", "aquatorial guinea", "aquatorialguinea", "aquatorial guinea", "aquatorialguinea", "aquatorial guinea", "aquatorialguinea", "equatorialguinea", "aquatorial guinea", "aquatorialguinea", "äquatorialguinea"],
    "ER": ["er", "eri", "eritrea", "eritrean"],
    "EE": ["ee", "est", "estonia", "estland"],
    "SZ": ["sz", "swz", "eswatini", "swaziland", "swasiland"],
    "ET": ["et", "eth", "ethiopia", "athopien", "äthiopien"],
    "FJ": ["fj", "fji", "fiji", "fidschi"],
    "FI": ["fi", "fin", "finland", "finnland"],
    "FR": ["fr", "fra", "france", "frankreich"],
    "GA": ["ga", "gab", "gabon"],
    "GM": ["gm", "gmb", "gambia", "the gambia"],
    "GE": ["ge", "geo", "georgia", "georgien"],
    "DE": ["de", "deu", "ger", "germany", "deutschland", "bundesrepublik deutschland", "brd", "d e"],
    "GH": ["gh", "gha", "ghana", "gana"],
    "GR": ["gr", "grc", "greece", "griechenland", "hellas", "hellenic republic"],
    "GD": ["gd", "grd", "grenada", "grenada"],
    "GT": ["gt", "gtm", "guatemala"],
    "GN": ["gn", "gin", "guinea", "guinea conakry"],
    "GW": ["gw", "gnb", "guinea bissau", "guinea bissau"],
    "GY": ["gy", "guy", "guyana"],
    "HT": ["ht", "hti", "haiti", "haïti"],
    "HN": ["hn", "hnd", "honduras"],
    "HU": ["hu", "hun", "hungary", "ungarn"],
    "IS": ["is", "isl", "iceland", "island", "íceland"],
    "IN": ["in", "ind", "india", "indien"],
    "ID": ["id", "idn", "indonesia", "indonesien"],
    "IR": ["ir", "irn", "iran", "iran islamic republic", "islamic republic of iran"],
    "IQ": ["iq", "irq", "iraq", "irak"],
    "IE": ["ie", "irl", "ireland", "irland"],
    "IL": ["il", "isr", "israel"],
    "IT": ["it", "ita", "italy", "italien"],
    "JM": ["jm", "jam", "jamaica", "jamaika"],
    "JP": ["jp", "jpn", "japan", "japan"],
    "JO": ["jo", "jor", "jordan", "jordanien"],
    "KZ": ["kz", "kaz", "kazakhstan", "kasachstan"],
    "KE": ["ke", "ken", "kenya", "kenia"],
    "KI": ["ki", "kir", "kiribati"],
    "KP": ["kp", "prk", "north korea", "north korea", "democratic people s republic of korea", "nordkorea"],
    "KR": ["kr", "kor", "south korea", "republic of korea", "korea republic", "sudkorea", "südkorea"],
    "KW": ["kw", "kwt", "kuwait", "kuwait"],
    "KG": ["kg", "kgz", "kyrgyzstan", "kyrgyz republic", "kirgisistan"],
    "LA": ["la", "lao", "laos", "lao people s democratic republic"],
    "LV": ["lv", "lva", "latvia", "lettland"],
    "LB": ["lb", "lbn", "lebanon", "libanon"],
    "LS": ["ls", "lso", "lesotho"],
    "LR": ["lr", "lbr", "liberia", "liberien"],
    "LY": ["ly", "lby", "libya", "libyen"],
    "LI": ["li", "lie", "liechtenstein"],
    "LT": ["lt", "ltu", "lithuania", "litauen"],
    "LU": ["lu", "lux", "luxembourg", "luxemburg"],
    "MG": ["mg", "mdg", "madagascar", "madagaskar"],
    "MW": ["mw", "mwi", "malawi"],
    "MY": ["my", "mys", "malaysia", "malaysien"],
    "MV": ["mv", "mdv", "maldives", "malediven"],
    "ML": ["ml", "mli", "mali"],
    "MT": ["mt", "mlt", "malta", "malta"],
    "MH": ["mh", "mhl", "marshall islands", "marshallinseln"],
    "MR": ["mr", "mrt", "mauritania", "mauretanien"],
    "MU": ["mu", "mus", "mauritius", "mauritius"],
    "MX": ["mx", "mex", "mexico", "mexiko"],
    "FM": ["fm", "fsm", "micronesia", "federated states of micronesia", "mikronesien"],
    "MD": ["md", "mda", "moldova", "republic of moldova", "republik moldau", "moldau"],
    "MC": ["mc", "mco", "monaco", "monako"],
    "MN": ["mn", "mng", "mongolia", "mongolei"],
    "ME": ["me", "mne", "montenegro"],
    "MA": ["ma", "mar", "morocco", "marokko"],
    "MZ": ["mz", "moz", "mozambique", "mosambik", "mosambik"],
    "MM": ["mm", "mmr", "myanmar", "burma", "birma"],
    "NA": ["na", "nam", "namibia", "namibien"],
    "NR": ["nr", "nru", "nauru"],
    "NP": ["np", "npl", "nepal", "nepal"],
    "NL": ["nl", "nld", "netherlands", "the netherlands", "holland", "niederlande"],
    "NZ": ["nz", "nzl", "new zealand", "neuseeland"],
    "NI": ["ni", "nic", "nicaragua", "nicaragua"],
    "NE": ["ne", "ner", "niger"],
    "NG": ["ng", "nga", "nigeria", "nigerien"],
    "MK": ["mk", "mkd", "north macedonia", "macedonia", "nordmazedonien", "mazedonien"],
    "NO": ["no", "nor", "norway", "norwegen"],
    "OM": ["om", "omn", "oman", "oman"],
    "PK": ["pk", "pak", "pakistan", "pakistan"],
    "PW": ["pw", "plw", "palau"],
    "PA": ["pa", "pan", "panama", "panama"],
    "PG": ["pg", "png", "papua new guinea", "papua neuguinea"],
    "PY": ["py", "pry", "paraguay"],
    "PE": ["pe", "per", "peru", "perú"],
    "PH": ["ph", "phl", "philippines", "philippinen"],
    "PL": ["pl", "pol", "poland", "polen"],
    "PT": ["pt", "prt", "portugal"],
    "QA": ["qa", "qat", "qatar", "katar"],
    "RO": ["ro", "rou", "romania", "rumania", "romänien"],
    "RU": ["ru", "rus", "russia", "russian federation", "russland"],
    "RW": ["rw", "rwa", "rwanda", "ruanda"],
    "KN": ["kn", "kna", "saint kitts and nevis", "st kitts and nevis", "st kitts nevis"],
    "LC": ["lc", "lca", "saint lucia", "st lucia"],
    "VC": ["vc", "vct", "saint vincent and the grenadines", "st vincent and the grenadines", "saint vincent grenadines"],
    "WS": ["ws", "wsm", "samoa"],
    "SM": ["sm", "smr", "san marino"],
    "ST": ["st", "stp", "sao tome and principe", "sao tome principe", "sao tome und principe"],
    "SA": ["sa", "sau", "saudi arabia", "saudi arabien", "saudiarabien"],
    "SN": ["sn", "sen", "senegal"],
    "RS": ["rs", "srb", "serbia", "serbien"],
    "SC": ["sc", "syc", "seychelles", "sechellen"],
    "SL": ["sl", "sle", "sierra leone"],
    "SG": ["sg", "sgp", "singapore", "singapur"],
    "SK": ["sk", "svk", "slovakia", "slowakei"],
    "SI": ["si", "svn", "slovenia", "slowenien"],
    "SB": ["sb", "slb", "solomon islands", "solomoninseln"],
    "SO": ["so", "som", "somalia", "somalia"],
    "ZA": ["za", "zaf", "south africa", "sudafrika", "südafrika", "rsa"],
    "SS": ["ss", "ssd", "south sudan", "sudsudan", "südsudan"],
    "ES": ["es", "esp", "spain", "spanien"],
    "LK": ["lk", "lka", "sri lanka"],
    "SD": ["sd", "sdn", "sudan", "sudan"],
    "SR": ["sr", "sur", "suriname", "surinam"],
    "SE": ["se", "swe", "sweden", "schweden"],
    "CH": ["ch", "che", "sui", "switzerland", "schweiz", "suisse", "svizzera"],
    "SY": ["sy", "syr", "syria", "syrian arab republic", "syrien"],
    "TW": ["tw", "twn", "taiwan", "taiwan province of china"],
    "TJ": ["tj", "tjk", "tajikistan", "tadschikistan"],
    "TZ": ["tz", "tza", "tanzania", "united republic of tanzania", "tansania"],
    "TH": ["th", "tha", "thailand", "thailand"],
    "TL": ["tl", "tls", "timor leste", "east timor", "osttimor"],
    "TG": ["tg", "tgo", "togo"],
    "TO": ["to", "ton", "tonga"],
    "TT": ["tt", "tto", "trinidad and tobago", "trinidad und tobago"],
    "TN": ["tn", "tun", "tunisia", "tunesien"],
    "TR": ["tr", "tur", "turkey", "turkiye", "türkiye", "turkei", "türkei"],
    "TM": ["tm", "tkm", "turkmenistan", "turkmenistan"],
    "TV": ["tv", "tuv", "tuvalu"],
    "UG": ["ug", "uga", "uganda", "uganda"],
    "UA": ["ua", "ukr", "ukraine", "ukraine"],
    "AE": ["ae", "are", "uae", "united arab emirates", "vereinigte arabische emirate", "v a e"],
    "GB": ["gb", "gbr", "uk", "u k", "united kingdom", "great britain", "britain", "england", "scotland", "wales", "northern ireland", "vereinigtes konigreich", "vereinigtes königreich", "grossbritannien", "großbritannien"],
    "US": ["us", "usa", "u s", "u s a", "united states", "united states of america", "america", "vereinigte staaten", "vereinigte staaten von amerika"],
    "UY": ["uy", "ury", "uruguay"],
    "UZ": ["uz", "uzb", "uzbekistan", "usbekistan"],
    "VU": ["vu", "vut", "vanuatu"],
    "VA": ["va", "vat", "vatican", "vatican city", "holy see", "vatikan", "vatikanstadt"],
    "VE": ["ve", "ven", "venezuela", "venezuela bolivarian republic"],
    "VN": ["vn", "vnm", "vietnam", "viet nam"],
    "YE": ["ye", "yem", "yemen", "jemen"],
    "ZM": ["zm", "zmb", "zambia", "sambia"],
    "ZW": ["zw", "zwe", "zimbabwe", "simbabwe"],
    "PS": ["ps", "pse", "palestine", "palestinian territories", "state of palestine", "palastina", "palästina"],
    "XK": ["xk", "xkx", "kosovo"],
}

alias_to_code = {}
ambiguous_aliases = set()

for code, aliases in country_aliases.items():
    for alias in aliases:
        normalized_alias = normalize_value(alias)
        if normalized_alias in alias_to_code and alias_to_code[normalized_alias] != code:
            ambiguous_aliases.add(normalized_alias)
        else:
            alias_to_code[normalized_alias] = code

for alias in ambiguous_aliases:
    alias_to_code.pop(alias, None)

def convert_country(value):
    normalized = normalize_value(value)
    if not normalized:
        return "UNKNOWN"
    return alias_to_code.get(normalized, "UNKNOWN")

df = pd.read_parquet(input_path)
df["country"] = df["country"].map(convert_country).astype("string")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)