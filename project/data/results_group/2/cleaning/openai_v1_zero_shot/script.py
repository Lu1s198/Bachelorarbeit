import os
import re
import unicodedata
from datetime import datetime, timezone

import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/customers_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/cleaning/openai_v1_zero_shot/output.parquet"

df = pd.read_csv(input_path)

for column in df.columns:
    if pd.api.types.is_object_dtype(df[column]) or pd.api.types.is_string_dtype(df[column]):
        df[column] = df[column].map(lambda value: value.strip() if isinstance(value, str) else value)

if "country" in df.columns:
    df["country"] = df["country"].fillna("UNKNOWN")

def parse_registered_at(value):
    if pd.isna(value):
        return pd.NaT

    value = str(value).strip()
    if not value:
        return pd.NaT

    if re.fullmatch(r"-?\d{10}(?:\.0+)?", value):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc).replace(tzinfo=None)
        except (ValueError, OverflowError, OSError):
            return pd.NaT

    formats = (
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d.%m.%Y",
        "%d-%m-%Y",
        "%B %d %Y",
        "%b %d %Y",
        "%B %d, %Y",
        "%b %d, %Y",
    )

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return pd.NaT

if "registered_at" in df.columns:
    parsed_dates = df["registered_at"].map(parse_registered_at)
    df["registered_at"] = pd.to_datetime(parsed_dates, errors="coerce").dt.strftime("%Y-%m-%d")
    df["registered_at"] = df["registered_at"].where(df["registered_at"].notna(), pd.NA)

def normalize_key(value):
    if pd.isna(value):
        return ""
    value = str(value).strip().casefold().replace("ß", "ss")
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()

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
    "AZ": ["az", "aze", "azerbaijan", "aserbaidschan"],
    "BS": ["bs", "bhs", "bahamas"],
    "BH": ["bh", "bhr", "bahrain", "bahrain"],
    "BD": ["bd", "bgd", "bangladesh", "bangladesch"],
    "BB": ["bb", "brb", "barbados"],
    "BY": ["by", "blr", "belarus", "weissrussland", "weißrussland"],
    "BE": ["be", "bel", "belgium", "belgien"],
    "BZ": ["bz", "blz", "belize"],
    "BJ": ["bj", "ben", "benin"],
    "BT": ["bt", "btn", "bhutan", "bhutan"],
    "BO": ["bo", "bol", "bolivia", "bolivien"],
    "BA": ["ba", "bih", "bosnia and herzegovina", "bosnien und herzegowina", "bosnia herzegovina"],
    "BW": ["bw", "bwa", "botswana"],
    "BR": ["br", "bra", "brazil", "brasilien", "brasil"],
    "BN": ["bn", "brn", "brunei"],
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
    "CN": ["cn", "chn", "china", "pr china", "people s republic of china", "volksrepublik china"],
    "CO": ["co", "col", "colombia", "kolumbien"],
    "KM": ["km", "com", "comoros", "komoren"],
    "CG": ["cg", "cog", "republic of the congo", "congo brazzaville", "republik kongo"],
    "CD": ["cd", "cod", "democratic republic of the congo", "dr congo", "congo kinshasa", "demokratische republik kongo"],
    "CR": ["cr", "cri", "costa rica"],
    "CI": ["ci", "civ", "ivory coast", "cote d ivoire", "côte d ivoire", "elfenbeinkuste", "elfenbeinküste"],
    "HR": ["hr", "hrv", "croatia", "kroatien"],
    "CU": ["cu", "cub", "cuba", "kuba"],
    "CY": ["cy", "cyp", "cyprus", "zypern"],
    "CZ": ["cz", "cze", "czech republic", "czechia", "tschechien", "tschechische republik"],
    "DK": ["dk", "dnk", "denmark", "danemark"],
    "DJ": ["dj", "dji", "djibouti", "dschibuti"],
    "DM": ["dm", "dma", "dominica", "dominica"],
    "DO": ["do", "dom", "dominican republic", "dominikanische republik"],
    "EC": ["ec", "ecu", "ecuador", "ecuador"],
    "EG": ["eg", "egy", "egypt", "agypten", "ägypten"],
    "SV": ["sv", "slv", "el salvador"],
    "GQ": ["gq", "gnq", "equatorial guinea", "aquatorialguinea", "äquatorialguinea"],
    "ER": ["er", "eri", "eritrea"],
    "EE": ["ee", "est", "estonia", "estland"],
    "SZ": ["sz", "swz", "eswatini", "swaziland"],
    "ET": ["et", "eth", "ethiopia", "athiopien", "äthiopien"],
    "FJ": ["fj", "fji", "fiji", "fidschi"],
    "FI": ["fi", "fin", "finland", "finnland"],
    "FR": ["fr", "fra", "fre", "france", "frankreich"],
    "GA": ["ga", "gab", "gabon"],
    "GM": ["gm", "gmb", "gambia"],
    "GE": ["ge", "geo", "georgia", "georgien"],
    "DE": ["de", "deu", "ger", "germany", "deutschland", "bundesrepublik deutschland", "brd"],
    "GH": ["gh", "gha", "ghana"],
    "GR": ["gr", "grc", "greece", "griechenland"],
    "GD": ["gd", "grd", "grenada"],
    "GT": ["gt", "gtm", "guatemala"],
    "GN": ["gn", "gin", "guinea", "guinea"],
    "GW": ["gw", "gnb", "guinea bissau"],
    "GY": ["gy", "guy", "guyana"],
    "HT": ["ht", "hti", "haiti"],
    "HN": ["hn", "hnd", "honduras"],
    "HU": ["hu", "hun", "hungary", "ungarn"],
    "IS": ["is", "isl", "iceland", "island", "island"],
    "IN": ["in", "ind", "india", "indien"],
    "ID": ["id", "idn", "indonesia", "indonesien"],
    "IR": ["ir", "irn", "iran", "iran"],
    "IQ": ["iq", "irq", "iraq", "irak"],
    "IE": ["ie", "irl", "ireland", "irland"],
    "IL": ["il", "isr", "israel"],
    "IT": ["it", "ita", "italy", "italien"],
    "JM": ["jm", "jam", "jamaica", "jamaika"],
    "JP": ["jp", "jpn", "japan"],
    "JO": ["jo", "jor", "jordan", "jordanien"],
    "KZ": ["kz", "kaz", "kazakhstan", "kasachstan"],
    "KE": ["ke", "ken", "kenya", "kenia"],
    "KI": ["ki", "kir", "kiribati"],
    "KP": ["kp", "prk", "north korea", "nordkorea"],
    "KR": ["kr", "kor", "south korea", "sudkorea", "republic of korea"],
    "KW": ["kw", "kwt", "kuwait", "kuwait"],
    "KG": ["kg", "kgz", "kyrgyzstan", "kirgisistan"],
    "LA": ["la", "lao", "laos"],
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
    "MT": ["mt", "mlt", "malta"],
    "MH": ["mh", "mhl", "marshall islands", "marshallinseln"],
    "MR": ["mr", "mrt", "mauritania", "mauretanien"],
    "MU": ["mu", "mus", "mauritius", "mauritius"],
    "MX": ["mx", "mex", "mexico", "mexiko"],
    "FM": ["fm", "fsm", "micronesia", "mikronesien"],
    "MD": ["md", "mda", "moldova", "moldawien"],
    "MC": ["mc", "mco", "monaco", "monako"],
    "MN": ["mn", "mng", "mongolia", "mongolei"],
    "ME": ["me", "mne", "montenegro"],
    "MA": ["ma", "mar", "morocco", "marokko"],
    "MZ": ["mz", "moz", "mozambique", "mosambik"],
    "MM": ["mm", "mmr", "myanmar", "burma"],
    "NA": ["na", "nam", "namibia", "namibien"],
    "NR": ["nr", "nru", "nauru"],
    "NP": ["np", "npl", "nepal"],
    "NL": ["nl", "nld", "netherlands", "holland", "niederlande"],
    "NZ": ["nz", "nzl", "new zealand", "neuseeland"],
    "NI": ["ni", "nic", "nicaragua", "nikaragua"],
    "NE": ["ne", "ner", "niger"],
    "NG": ["ng", "nga", "nigeria", "nigerien"],
    "MK": ["mk", "mkd", "north macedonia", "nordmazedonien", "macedonia", "mazedonien"],
    "NO": ["no", "nor", "norway", "norwegen"],
    "OM": ["om", "omn", "oman"],
    "PK": ["pk", "pak", "pakistan"],
    "PW": ["pw", "plw", "palau"],
    "PA": ["pa", "pan", "panama"],
    "PG": ["pg", "png", "papua new guinea", "papua neuguinea"],
    "PY": ["py", "pry", "paraguay"],
    "PE": ["pe", "per", "peru"],
    "PH": ["ph", "phl", "philippines", "philippinen"],
    "PL": ["pl", "pol", "poland", "polen"],
    "PT": ["pt", "prt", "portugal"],
    "QA": ["qa", "qat", "qatar", "katar"],
    "RO": ["ro", "rou", "romania", "rumania", "rumänien"],
    "RU": ["ru", "rus", "russia", "russian federation", "russland"],
    "RW": ["rw", "rwa", "rwanda", "ruanda"],
    "KN": ["kn", "kna", "saint kitts and nevis", "st kitts and nevis"],
    "LC": ["lc", "lca", "saint lucia", "st lucia"],
    "VC": ["vc", "vct", "saint vincent and the grenadines", "st vincent and the grenadines"],
    "WS": ["ws", "wsm", "samoa"],
    "SM": ["sm", "smr", "san marino"],
    "ST": ["st", "stp", "sao tome and principe", "são tomé and príncipe"],
    "SA": ["sa", "sau", "saudi arabia", "saudi arabien"],
    "SN": ["sn", "sen", "senegal"],
    "RS": ["rs", "srb", "serbia", "serbien"],
    "SC": ["sc", "syc", "seychelles", "seyschellen"],
    "SL": ["sl", "sle", "sierra leone"],
    "SG": ["sg", "sgp", "singapore", "singapur"],
    "SK": ["sk", "svk", "slovakia", "slowakei"],
    "SI": ["si", "svn", "slovenia", "slowenien"],
    "SB": ["sb", "slb", "solomon islands", "salomonen"],
    "SO": ["so", "som", "somalia", "somalia"],
    "ZA": ["za", "zaf", "south africa", "sudafrika"],
    "SS": ["ss", "ssd", "south sudan", "sudsudan"],
    "ES": ["es", "esp", "spain", "spanien"],
    "LK": ["lk", "lka", "sri lanka"],
    "SD": ["sd", "sdn", "sudan"],
    "SR": ["sr", "sur", "suriname", "surinam"],
    "SE": ["se", "swe", "sweden", "schweden"],
    "CH": ["ch", "che", "switzerland", "schweiz"],
    "SY": ["sy", "syr", "syria", "syrien"],
    "TW": ["tw", "twn", "taiwan"],
    "TJ": ["tj", "tjk", "tajikistan", "tadschikistan"],
    "TZ": ["tz", "tza", "tanzania", "tansania"],
    "TH": ["th", "tha", "thailand", "thailand"],
    "TL": ["tl", "tls", "timor leste", "east timor", "osttimor"],
    "TG": ["tg", "tgo", "togo"],
    "TO": ["to", "ton", "tonga"],
    "TT": ["tt", "tto", "trinidad and tobago", "trinidad und tobago"],
    "TN": ["tn", "tun", "tunisia", "tunesien"],
    "TR": ["tr", "tur", "turkey", "turkiye", "türkei"],
    "TM": ["tm", "tkm", "turkmenistan", "turkmenistan"],
    "TV": ["tv", "tuv", "tuvalu"],
    "UG": ["ug", "uga", "uganda"],
    "UA": ["ua", "ukr", "ukraine", "ukraine"],
    "AE": ["ae", "are", "united arab emirates", "uae", "vereinigte arabische emirate"],
    "GB": ["gb", "gbr", "uk", "u k", "united kingdom", "great britain", "england", "scotland", "wales", "grossbritannien", "großbritannien", "vereinigtes konigreich", "vereinigtes königreich"],
    "US": ["us", "usa", "u s a", "united states", "united states of america", "america", "vereinigte staaten"],
    "UY": ["uy", "ury", "uruguay"],
    "UZ": ["uz", "uzb", "uzbekistan", "usbekistan"],
    "VU": ["vu", "vut", "vanuatu"],
    "VA": ["va", "vat", "vatican", "vatican city", "vatikan", "heiliger stuhl"],
    "VE": ["ve", "ven", "venezuela"],
    "VN": ["vn", "vnm", "vietnam", "viet nam"],
    "YE": ["ye", "yem", "yemen", "jemen"],
    "ZM": ["zm", "zmb", "zambia", "sambia"],
    "ZW": ["zw", "zwe", "zimbabwe", "simbabwe"],
}

country_lookup = {}
for code, aliases in country_aliases.items():
    for alias in aliases:
        country_lookup[normalize_key(alias)] = code

if "country" in df.columns:
    df["country"] = df["country"].map(lambda value: country_lookup.get(normalize_key(value), "UNKNOWN"))

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)