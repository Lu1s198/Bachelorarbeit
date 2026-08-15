import os
import re
import unicodedata
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/customers_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/cleaning/openai_v2_few_shot/output.parquet"

df = pd.read_csv(input_path)

text_columns = df.select_dtypes(include=["object", "string"]).columns
for column in text_columns:
    df[column] = df[column].astype("string").str.strip()

df["country"] = df["country"].fillna("UNKNOWN").replace("", "UNKNOWN")

registered = df["registered_at"].astype("string").str.strip()
parsed_dates = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")

unix_mask = registered.str.fullmatch(r"\d{9,12}", na=False)
parsed_dates.loc[unix_mask] = pd.to_datetime(
    pd.to_numeric(registered.loc[unix_mask], errors="coerce"),
    unit="s",
    errors="coerce"
)

iso_mask = registered.str.fullmatch(r"\d{4}-\d{2}-\d{2}", na=False)
parsed_dates.loc[iso_mask] = pd.to_datetime(
    registered.loc[iso_mask],
    format="%Y-%m-%d",
    errors="coerce"
)

german_mask = registered.str.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{4}", na=False)
parsed_dates.loc[german_mask] = pd.to_datetime(
    registered.loc[german_mask],
    format="%d.%m.%Y",
    errors="coerce"
)

remaining_mask = parsed_dates.isna() & registered.notna()
parsed_dates.loc[remaining_mask] = pd.to_datetime(
    registered.loc[remaining_mask],
    errors="coerce"
)

df["registered_at"] = parsed_dates.dt.strftime("%Y-%m-%d")

def normalize_country_value(value):
    value = str(value).strip().casefold()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", "", value)

country_lookup = {}

try:
    import pycountry

    for country in pycountry.countries:
        code = country.alpha_2.upper()
        for attribute in ["alpha_2", "alpha_3", "name", "official_name", "common_name"]:
            if hasattr(country, attribute):
                country_lookup[normalize_country_value(getattr(country, attribute))] = code
except ImportError:
    pass

country_aliases = {
    "DE": [
        "de", "deu", "germany", "deutschland", "federal republic of germany",
        "bundesrepublik deutschland"
    ],
    "AT": ["at", "aut", "austria", "osterreich", "österreich"],
    "CH": ["ch", "che", "switzerland", "schweiz", "suisse", "svizzera"],
    "US": [
        "us", "usa", "u s", "u s a", "united states", "united states of america",
        "amerika", "america", "vereinigte staaten", "vereinigte staaten von amerika"
    ],
    "GB": [
        "gb", "gbr", "uk", "u k", "united kingdom", "great britain",
        "britain", "england", "grossbritannien", "großbritannien",
        "vereinigtes konigreich", "vereinigtes königreich"
    ],
    "FR": ["fr", "fra", "france", "frankreich"],
    "IT": ["it", "ita", "italy", "italien"],
    "ES": ["es", "esp", "spain", "spanien"],
    "PT": ["pt", "prt", "portugal"],
    "NL": ["nl", "nld", "netherlands", "holland", "niederlande"],
    "BE": ["be", "bel", "belgium", "belgien"],
    "LU": ["lu", "lux", "luxembourg", "luxemburg"],
    "DK": ["dk", "dnk", "denmark", "dänemark", "danemark"],
    "SE": ["se", "swe", "sweden", "schweden"],
    "NO": ["no", "nor", "norway", "norwegen"],
    "FI": ["fi", "fin", "finland", "finnland"],
    "IS": ["is", "isl", "iceland", "island", "island"],
    "IE": ["ie", "irl", "ireland", "irland"],
    "PL": ["pl", "pol", "poland", "polen"],
    "CZ": ["cz", "cze", "czechia", "czech republic", "tschechien", "tschechische republik"],
    "SK": ["sk", "svk", "slovakia", "slowakei"],
    "HU": ["hu", "hun", "hungary", "ungarn"],
    "RO": ["ro", "rou", "romania", "rumänien", "rumanien"],
    "BG": ["bg", "bgr", "bulgaria", "bulgarien"],
    "HR": ["hr", "hrv", "croatia", "kroatien"],
    "SI": ["si", "svn", "slovenia", "slowenien"],
    "RS": ["rs", "srb", "serbia", "serbien"],
    "BA": ["ba", "bih", "bosnia and herzegovina", "bosnien und herzegowina"],
    "ME": ["me", "mne", "montenegro"],
    "AL": ["al", "alb", "albania", "albanien"],
    "MK": ["mk", "mkd", "north macedonia", "nordmazedonien", "mazedonien"],
    "GR": ["gr", "grc", "greece", "griechenland", "hellas"],
    "TR": ["tr", "tur", "turkey", "türkiye", "turkiye", "tuerkei", "türkei"],
    "UA": ["ua", "ukr", "ukraine"],
    "BY": ["by", "blr", "belarus", "weißrussland", "weissrussland"],
    "MD": ["md", "mda", "moldova", "moldawien"],
    "LT": ["lt", "ltu", "lithuania", "litauen"],
    "LV": ["lv", "lva", "latvia", "lettland"],
    "EE": ["ee", "est", "estonia", "estland"],
    "RU": ["ru", "rus", "russia", "russian federation", "russland"],
    "CA": ["ca", "can", "canada"],
    "MX": ["mx", "mex", "mexico", "mexiko"],
    "BR": ["br", "bra", "brazil", "brasilien"],
    "AR": ["ar", "arg", "argentina", "argentinien"],
    "CL": ["cl", "chl", "chile"],
    "CO": ["co", "col", "colombia", "kolumbien"],
    "PE": ["pe", "per", "peru", "perú"],
    "VE": ["ve", "ven", "venezuela"],
    "AU": ["au", "aus", "australia", "australien"],
    "NZ": ["nz", "nzl", "new zealand", "neuseeland"],
    "CN": ["cn", "chn", "china", "volksrepublik china"],
    "JP": ["jp", "jpn", "japan"],
    "KR": ["kr", "kor", "south korea", "republic of korea", "südkorea", "suedkorea"],
    "KP": ["kp", "prk", "north korea", "democratic peoples republic of korea", "nordkorea"],
    "IN": ["in", "ind", "india", "indien"],
    "ID": ["id", "idn", "indonesia", "indonesien"],
    "MY": ["my", "mys", "malaysia", "malaysien"],
    "SG": ["sg", "sgp", "singapore", "singapur"],
    "TH": ["th", "tha", "thailand", "thailand"],
    "VN": ["vn", "vnm", "vietnam"],
    "PH": ["ph", "phl", "philippines", "philippinen"],
    "PK": ["pk", "pak", "pakistan"],
    "BD": ["bd", "bgd", "bangladesh", "bangladesch"],
    "AE": ["ae", "are", "united arab emirates", "uae", "vereinigte arabische emirate"],
    "SA": ["sa", "sau", "saudi arabia", "saudi arabien"],
    "IL": ["il", "isr", "israel"],
    "IR": ["ir", "irn", "iran"],
    "IQ": ["iq", "irq", "iraq", "irak"],
    "EG": ["eg", "egy", "egypt", "ägypten", "agypten"],
    "ZA": ["za", "zaf", "south africa", "südafrika", "suedafrika"],
    "NG": ["ng", "nga", "nigeria", "nigerien"],
    "KE": ["ke", "ken", "kenya", "kenia"],
    "MA": ["ma", "mar", "morocco", "marokko"],
    "TN": ["tn", "tun", "tunisia", "tunesien"],
    "DZ": ["dz", "dza", "algeria", "algerien"],
    "GH": ["gh", "gha", "ghana"],
    "TZ": ["tz", "tza", "tanzania", "tansania"],
    "ET": ["et", "eth", "ethiopia", "äthiopien", "athiopien"],
    "UNKNOWN": ["unknown", "unbekannt", "n a", "na", "none", "null", "nan", ""]
}

for code, aliases in country_aliases.items():
    for alias in aliases:
        country_lookup[normalize_country_value(alias)] = code

normalized_countries = df["country"].map(normalize_country_value)
df["country"] = normalized_countries.map(country_lookup).fillna("UNKNOWN")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)