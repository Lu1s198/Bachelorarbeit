import os
import re
import unicodedata
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/customers_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/cleaning/openai_v2_few_shot_r2/output.parquet"

df = pd.read_csv(input_path)

text_columns = df.select_dtypes(include=["object", "string"]).columns
for column in text_columns:
    df[column] = df[column].astype("string").str.strip()

df["country"] = df["country"].fillna("UNKNOWN").replace("", "UNKNOWN")

def parse_registered_at(value):
    if pd.isna(value) or str(value).strip() == "":
        return pd.NaT

    value = str(value).strip()

    if re.fullmatch(r"\d{9,11}", value):
        return pd.to_datetime(value, unit="s", errors="coerce")

    formats = [
        "%Y-%m-%d",
        "%d.%m.%Y",
        "%B %d %Y",
        "%b %d %Y",
        "%B %d, %Y",
        "%b %d, %Y",
    ]

    for date_format in formats:
        parsed = pd.to_datetime(value, format=date_format, errors="coerce")
        if not pd.isna(parsed):
            return parsed

    return pd.to_datetime(value, errors="coerce")

df["registered_at"] = df["registered_at"].map(parse_registered_at).map(
    lambda value: value.strftime("%Y-%m-%d") if not pd.isna(value) else pd.NA
)

def normalize_country_key(value):
    value = str(value).strip().lower().replace("ß", "ss")
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]", "", value)

country_groups = {
    "DE": ["DE", "DEU", "GER", "Germany", "Deutschland", "Bundesrepublik Deutschland"],
    "AT": ["AT", "AUT", "Austria", "Österreich", "Oesterreich"],
    "CH": ["CH", "CHE", "SUI", "Switzerland", "Schweiz", "Suisse", "Svizzera"],
    "US": ["US", "USA", "United States", "United States of America", "America", "USA", "U.S.", "U.S.A."],
    "GB": ["GB", "UK", "GBR", "United Kingdom", "Great Britain", "England", "Britain", "Vereinigtes Königreich", "Grossbritannien"],
    "FR": ["FR", "FRA", "France", "Frankreich"],
    "IT": ["IT", "ITA", "Italy", "Italien"],
    "ES": ["ES", "ESP", "Spain", "Spanien"],
    "PT": ["PT", "PRT", "Portugal"],
    "NL": ["NL", "NLD", "Netherlands", "Holland", "Niederlande"],
    "BE": ["BE", "BEL", "Belgium", "Belgien"],
    "LU": ["LU", "LUX", "Luxembourg", "Luxemburg"],
    "DK": ["DK", "DNK", "Denmark", "Dänemark", "Daenemark"],
    "SE": ["SE", "SWE", "Sweden", "Schweden"],
    "NO": ["NO", "NOR", "Norway", "Norwegen"],
    "FI": ["FI", "FIN", "Finland", "Finnland"],
    "IE": ["IE", "IRL", "Ireland", "Irland"],
    "PL": ["PL", "POL", "Poland", "Polen"],
    "CZ": ["CZ", "CZE", "Czech Republic", "Czechia", "Tschechien"],
    "SK": ["SK", "SVK", "Slovakia", "Slowakei"],
    "HU": ["HU", "HUN", "Hungary", "Ungarn"],
    "RO": ["RO", "ROU", "Romania", "Rumänien", "Rumaenien"],
    "BG": ["BG", "BGR", "Bulgaria", "Bulgarien"],
    "GR": ["GR", "GRC", "Greece", "Griechenland"],
    "HR": ["HR", "HRV", "Croatia", "Kroatien"],
    "SI": ["SI", "SVN", "Slovenia", "Slowenien"],
    "RS": ["RS", "SRB", "Serbia", "Serbien"],
    "BA": ["BA", "BIH", "Bosnia and Herzegovina", "Bosnien und Herzegowina"],
    "UA": ["UA", "UKR", "Ukraine"],
    "RU": ["RU", "RUS", "Russia", "Russian Federation", "Russland"],
    "TR": ["TR", "TUR", "Turkey", "Türkiye", "Turkiye", "Türkei", "Tuerkei"],
    "CA": ["CA", "CAN", "Canada", "Kanada"],
    "MX": ["MX", "MEX", "Mexico", "Mexiko"],
    "BR": ["BR", "BRA", "Brazil", "Brasilien"],
    "AR": ["AR", "ARG", "Argentina", "Argentinien"],
    "CL": ["CL", "CHL", "Chile"],
    "CO": ["CO", "COL", "Colombia", "Kolumbien"],
    "AU": ["AU", "AUS", "Australia", "Australien"],
    "NZ": ["NZ", "NZL", "New Zealand", "Neuseeland"],
    "JP": ["JP", "JPN", "Japan"],
    "CN": ["CN", "CHN", "China", "People's Republic of China", "Volksrepublik China"],
    "KR": ["KR", "KOR", "South Korea", "Republic of Korea", "Südkorea", "Suedkorea"],
    "IN": ["IN", "IND", "India", "Indien"],
    "ID": ["ID", "IDN", "Indonesia", "Indonesien"],
    "SG": ["SG", "SGP", "Singapore", "Singapur"],
    "MY": ["MY", "MYS", "Malaysia"],
    "TH": ["TH", "THA", "Thailand"],
    "VN": ["VN", "VNM", "Vietnam", "Viet Nam"],
    "PH": ["PH", "PHL", "Philippines", "Philippinen"],
    "AE": ["AE", "ARE", "United Arab Emirates", "UAE", "Vereinigte Arabische Emirate"],
    "SA": ["SA", "SAU", "Saudi Arabia", "Saudi-Arabien"],
    "IL": ["IL", "ISR", "Israel"],
    "EG": ["EG", "EGY", "Egypt", "Ägypten", "Aegypten"],
    "ZA": ["ZA", "ZAF", "South Africa", "Südafrika", "Suedafrika"],
    "NG": ["NG", "NGA", "Nigeria"],
    "KE": ["KE", "KEN", "Kenya", "Kenia"],
    "MA": ["MA", "MAR", "Morocco", "Marokko"],
}

country_map = {}
for code, aliases in country_groups.items():
    for alias in aliases:
        country_map[normalize_country_key(alias)] = code

df["country"] = df["country"].map(
    lambda value: country_map.get(normalize_country_key(value), "UNKNOWN")
)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)