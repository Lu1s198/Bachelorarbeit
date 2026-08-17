import os
import re
import unicodedata
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/customers_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/cleaning/openai_v1_zero_shot_r2/output.parquet"

df = pd.read_csv(input_path)

text_columns = df.select_dtypes(include=["object", "string"]).columns
for column in text_columns:
    df[column] = df[column].astype("string").str.strip()

if "country" in df.columns:
    df["country"] = df["country"].fillna("UNKNOWN")
    df.loc[df["country"].eq(""), "country"] = "UNKNOWN"

def parse_registered_at(value):
    if pd.isna(value):
        return pd.NaT

    text = str(value).strip()
    if not text:
        return pd.NaT

    if re.fullmatch(r"[+-]?\d{9,11}(?:\.0+)?", text):
        try:
            return pd.to_datetime(float(text), unit="s", errors="coerce")
        except Exception:
            return pd.NaT

    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%B %d %Y", "%b %d %Y"):
        try:
            parsed = pd.to_datetime(text, format=fmt, errors="coerce")
            if not pd.isna(parsed):
                return parsed
        except Exception:
            pass

    try:
        return pd.to_datetime(text, errors="coerce")
    except Exception:
        return pd.NaT

if "registered_at" in df.columns:
    parsed_dates = df["registered_at"].map(parse_registered_at)
    df["registered_at"] = parsed_dates.map(
        lambda x: x.strftime("%Y-%m-%d") if not pd.isna(x) else pd.NA
    ).astype("string")

def country_key(value):
    if pd.isna(value):
        return ""
    value = str(value).strip()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.upper().replace("&", "AND")
    return re.sub(r"[^A-Z0-9]", "", value)

country_aliases = {
    "AF": ["AF", "AFG", "AFGHANISTAN"],
    "AL": ["AL", "ALB", "ALBANIA", "ALBANIEN"],
    "DZ": ["DZ", "DZA", "ALGERIA", "ALGERIEN"],
    "AD": ["AD", "AND", "ANDORRA"],
    "AO": ["AO", "AGO", "ANGOLA"],
    "AG": ["AG", "ATG", "ANTIGUA", "ANTIGUAAND BARBUDA", "ANTIGUAUND BARBUDA"],
    "AR": ["AR", "ARG", "ARGENTINA", "ARGENTINIEN"],
    "AM": ["AM", "ARM", "ARMENIA", "ARMENIEN"],
    "AU": ["AU", "AUS", "AUSTRALIA", "AUSTRALIEN"],
    "AT": ["AT", "AUT", "AUSTRIA", "OESTERREICH", "OSTERREICH"],
    "AZ": ["AZ", "AZE", "AZERBAIJAN", "ASERBAIDSCHAN"],
    "BS": ["BS", "BHS", "BAHAMAS"],
    "BH": ["BH", "BHR", "BAHRAIN", "BAHREIN"],
    "BD": ["BD", "BGD", "BANGLADESH"],
    "BB": ["BB", "BRB", "BARBADOS"],
    "BY": ["BY", "BLR", "BELARUS", "WEISSRUSSLAND"],
    "BE": ["BE", "BEL", "BELGIUM", "BELGIEN"],
    "BZ": ["BZ", "BLZ", "BELIZE"],
    "BJ": ["BJ", "BEN", "BENIN"],
    "BT": ["BT", "BTN", "BHUTAN"],
    "BO": ["BO", "BOL", "BOLIVIA", "BOLIVIEN"],
    "BA": ["BA", "BIH", "BOSNIA", "BOSNIAANDHERZEGOVINA", "BOSNIENUNDHERZEGOWINA"],
    "BW": ["BW", "BWA", "BOTSWANA"],
    "BR": ["BR", "BRA", "BRAZIL", "BRASILIEN"],
    "BN": ["BN", "BRN", "BRUNEI"],
    "BG": ["BG", "BGR", "BULGARIA", "BULGARIEN"],
    "BF": ["BF", "BFA", "BURKINAFASO"],
    "BI": ["BI", "BDI", "BURUNDI"],
    "CV": ["CV", "CPV", "CABOVERDE", "CAPEVERDE", "KAPVERDE"],
    "KH": ["KH", "KHM", "CAMBODIA", "KAMBODSCHA"],
    "CM": ["CM", "CMR", "CAMEROON", "KAMERUN"],
    "CA": ["CA", "CAN", "CANADA", "KANADA"],
    "CF": ["CF", "CAF", "CENTRALAFRICANREPUBLIC", "ZENTRALAFRIKANISCHEREPUBLIK"],
    "TD": ["TD", "TCD", "CHAD", "TSCHAD"],
    "CL": ["CL", "CHL", "CHILE"],
    "CN": ["CN", "CHN", "CHINA", "PEOPLESREPUBLICOFCHINA", "VOLKSREPUBLIKCHINA"],
    "CO": ["CO", "COL", "COLOMBIA", "KOLUMBIEN"],
    "KM": ["KM", "COM", "COMOROS", "KOMOREN"],
    "CG": ["CG", "COG", "CONGO", "REPUBLICOFTHECONGO", "REPUBLIKKONGO", "CONGOBRAZZAVILLE"],
    "CD": ["CD", "COD", "DRC", "DEMOCRATICREPUBLICOFTHECONGO", "DEMOKRATISCHEREPUBLIKKONGO", "CONGOKINSHASA"],
    "CR": ["CR", "CRI", "COSTARICA"],
    "CI": ["CI", "CIV", "IVORYCOAST", "COTEDIVOIRE", "ELFENBEINKUESTE", "ELFENBEINKUSTE"],
    "HR": ["HR", "HRV", "CROATIA", "KROATIEN"],
    "CU": ["CU", "CUB", "CUBA", "KUBA"],
    "CY": ["CY", "CYP", "CYPRUS", "ZYPERN"],
    "CZ": ["CZ", "CZE", "CZECHIA", "CZECHREPUBLIC", "TSCHECHIEN", "TSCHECHISCHEREPUBLIK"],
    "DK": ["DK", "DNK", "DENMARK", "DAENEMARK", "DANEMARK"],
    "DJ": ["DJ", "DJI", "DJIBOUTI", "DSCHIBUTI"],
    "DM": ["DM", "DMA", "DOMINICA"],
    "DO": ["DO", "DOM", "DOMINICANREPUBLIC", "DOMINIKANISCHEREPUBLIK"],
    "EC": ["EC", "ECU", "ECUADOR"],
    "EG": ["EG", "EGY", "EGYPT", "AEGYPTEN", "AGYPTEN"],
    "SV": ["SV", "SLV", "ELSALVADOR"],
    "GQ": ["GQ", "GNQ", "EQUATORIALGUINEA", "AEQUATORIALGUINEA"],
    "ER": ["ER", "ERI", "ERITREA"],
    "EE": ["EE", "EST", "ESTONIA", "ESTLAND"],
    "SZ": ["SZ", "SWZ", "ESWATINI", "SWAZILAND"],
    "ET": ["ET", "ETH", "ETHIOPIA", "AETHIOPIEN", "ATHIOPIEN"],
    "FJ": ["FJ", "FJI", "FIJI", "FIDSCHI"],
    "FI": ["FI", "FIN", "FINLAND", "FINNLAND"],
    "FR": ["FR", "FRA", "FRANCE", "FRANKREICH"],
    "GA": ["GA", "GAB", "GABON"],
    "GM": ["GM", "GMB", "GAMBIA"],
    "GE": ["GE", "GEO", "GEORGIA", "GEORGIEN"],
    "DE": ["DE", "DEU", "GER", "GERMANY", "DEUTSCHLAND", "BUNDESREPUBLIKDEUTSCHLAND"],
    "GH": ["GH", "GHA", "GHANA"],
    "GR": ["GR", "GRC", "GREECE", "GRIECHENLAND", "HELLAS"],
    "GD": ["GD", "GRD", "GRENADA"],
    "GT": ["GT", "GTM", "GUATEMALA"],
    "GN": ["GN", "GIN", "GUINEA"],
    "GW": ["GW", "GNB", "GUINEABISSAU"],
    "GY": ["GY", "GUY", "GUYANA"],
    "HT": ["HT", "HTI", "HAITI"],
    "HN": ["HN", "HND", "HONDURAS"],
    "HU": ["HU", "HUN", "HUNGARY", "UNGARN"],
    "IS": ["IS", "ISL", "ICELAND", "ISLAND"],
    "IN": ["IN", "IND", "INDIA", "INDIEN"],
    "ID": ["ID", "IDN", "INDONESIA", "INDONESIEN"],
    "IR": ["IR", "IRN", "IRAN"],
    "IQ": ["IQ", "IRQ", "IRAQ", "IRAK"],
    "IE": ["IE", "IRL", "IRELAND", "IRLAND"],
    "IL": ["IL", "ISR", "ISRAEL"],
    "IT": ["IT", "ITA", "ITALY", "ITALIEN"],
    "JM": ["JM", "JAM", "JAMAICA", "JAMAIKA"],
    "JP": ["JP", "JPN", "JAPAN", "JAPAN"],
    "JO": ["JO", "JOR", "JORDAN", "JORDANIEN"],
    "KZ": ["KZ", "KAZ", "KAZAKHSTAN", "KASACHSTAN"],
    "KE": ["KE", "KEN", "KENYA", "KENIA"],
    "KI": ["KI", "KIR", "KIRIBATI"],
    "KP": ["KP", "PRK", "NORTHKOREA", "NORDKOREA"],
    "KR": ["KR", "KOR", "SOUTHKOREA", "SOUTHKOREA", "REPUBLICOFKOREA", "SUEDKOREA", "SUDKOREA"],
    "KW": ["KW", "KWT", "KUWAIT"],
    "KG": ["KG", "KGZ", "KYRGYZSTAN", "KIRGISISTAN"],
    "LA": ["LA", "LAO", "LAOS"],
    "LV": ["LV", "LVA", "LATVIA", "LETTLAND"],
    "LB": ["LB", "LBN", "LEBANON", "LIBANON"],
    "LS": ["LS", "LSO", "LESOTHO"],
    "LR": ["LR", "LBR", "LIBERIA"],
    "LY": ["LY", "LBY", "LIBYA", "LIBYEN"],
    "LI": ["LI", "LIE", "LIECHTENSTEIN"],
    "LT": ["LT", "LTU", "LITHUANIA", "LITAUEN"],
    "LU": ["LU", "LUX", "LUXEMBOURG"],
    "MG": ["MG", "MDG", "MADAGASCAR"],
    "MW": ["MW", "MWI", "MALAWI"],
    "MY": ["MY", "MYS", "MALAYSIA", "MALAYSIA"],
    "MV": ["MV", "MDV", "MALDIVES", "MALEDIVEN"],
    "ML": ["ML", "MLI", "MALI"],
    "MT": ["MT", "MLT", "MALTA"],
    "MH": ["MH", "MHL", "MARSHALLISLANDS", "MARSHALLINSELN"],
    "MR": ["MR", "MRT", "MAURITANIA", "MAURETANIEN"],
    "MU": ["MU", "MUS", "MAURITIUS"],
    "MX": ["MX", "MEX", "MEXICO", "MEXIKO"],
    "FM": ["FM", "FSM", "MICRONESIA", "MIKRONESIEN"],
    "MD": ["MD", "MDA", "MOLDOVA", "MOLDAWIEN"],
    "MC": ["MC", "MCO", "MONACO", "MONAKO"],
    "MN": ["MN", "MNG", "MONGOLIA", "MONGOLEI"],
    "ME": ["ME", "MNE", "MONTENEGRO"],
    "MA": ["MA", "MAR", "MOROCCO", "MAROKKO"],
    "MZ": ["MZ", "MOZ", "MOZAMBIQUE", "MOSAMBIK"],
    "MM": ["MM", "MMR", "MYANMAR", "BURMA"],
    "NA": ["NA", "NAM", "NAMIBIA", "NAMIBIEN"],
    "NR": ["NR", "NRU", "NAURU"],
    "NP": ["NP", "NPL", "NEPAL"],
    "NL": ["NL", "NLD", "NETHERLANDS", "HOLLAND", "NIEDERLANDE"],
    "NZ": ["NZ", "NZL", "NEWZEALAND", "NEUSEELAND"],
    "NI": ["NI", "NIC", "NICARAGUA"],
    "NE": ["NE", "NER", "NIGER"],
    "NG": ["NG", "NGA", "NIGERIA", "NIGERIA"],
    "MK": ["MK", "MKD", "NORTHMACEDONIA", "NORDMAZEDONIEN", "MACEDONIA", "MAZEDONIEN"],
    "NO": ["NO", "NOR", "NORWAY", "NORWEGEN"],
    "OM": ["OM", "OMN", "OMAN"],
    "PK": ["PK", "PAK", "PAKISTAN"],
    "PW": ["PW", "PLW", "PALAU"],
    "PA": ["PA", "PAN", "PANAMA"],
    "PG": ["PG", "PNG", "PAPUANEWGUINEA", "PAPUANEUGUINEA"],
    "PY": ["PY", "PRY", "PARAGUAY"],
    "PE": ["PE", "PER", "PERU"],
    "PH": ["PH", "PHL", "PHILIPPINES", "PHILIPPINEN"],
    "PL": ["PL", "POL", "POLAND", "POLEN"],
    "PT": ["PT", "PRT", "PORTUGAL"],
    "QA": ["QA", "QAT", "QATAR"],
    "RO": ["RO", "ROU", "ROM", "ROMANIA", "RUMAENIEN", "RUMANIEN"],
    "RU": ["RU", "RUS", "RUSSIA", "RUSSIANFEDERATION", "RUSSLAND"],
    "RW": ["RW", "RWA", "RWANDA"],
    "KN": ["KN", "KNA", "SAINTKITTSANDNEVIS"],
    "LC": ["LC", "LCA", "SAINTLUCIA"],
    "VC": ["VC", "VCT", "SAINTVINCENTANDTHEGRENADINES"],
    "WS": ["WS", "WSM", "SAMOA"],
    "SM": ["SM", "SMR", "SANMARINO"],
    "ST": ["ST", "STP", "SAOTOMEANDPRINCIPE"],
    "SA": ["SA", "SAU", "SAUDIARABIA", "SAUDIARABIEN"],
    "SN": ["SN", "SEN", "SENEGAL"],
    "RS": ["RS", "SRB", "SERBIA", "SERBIEN"],
    "SC": ["SC", "SYC", "SEYCHELLES", "SESCHELLEN"],
    "SL": ["SL", "SLE", "SIERRALEONE"],
    "SG": ["SG", "SGP", "SINGAPORE", "SINGAPUR"],
    "SK": ["SK", "SVK", "SLOVAKIA", "SLOWAKEI"],
    "SI": ["SI", "SVN", "SLOVENIA", "SLOWENIEN"],
    "SB": ["SB", "SLB", "SOLOMONISLANDS", "SALOMONINSELN"],
    "SO": ["SO", "SOM", "SOMALIA"],
    "ZA": ["ZA", "ZAF", "SOUTHAFRICA", "SUEDAFRIKA", "SUDAFRIKA"],
    "SS": ["SS", "SSD", "SOUTHSUDAN", "SUEDSUDAN", "SUDSUDAN"],
    "ES": ["ES", "ESP", "SPAIN", "SPANIEN"],
    "LK": ["LK", "LKA", "SRILANKA"],
    "SD": ["SD", "SDN", "SUDAN"],
    "SR": ["SR", "SUR", "SURINAME"],
    "SE": ["SE", "SWE", "SWEDEN", "SCHWEDEN"],
    "CH": ["CH", "CHE", "SWITZERLAND", "SCHWEIZ"],
    "SY": ["SY", "SYR", "SYRIA", "SYRIEN"],
    "TW": ["TW", "TWN", "TAIWAN"],
    "TJ": ["TJ", "TJK", "TAJIKISTAN", "TADSCHIKISTAN"],
    "TZ": ["TZ", "TZA", "TANZANIA", "TANSANIA"],
    "TH": ["TH", "THA", "THAILAND"],
    "TL": ["TL", "TLS", "TIMORLESTE", "EASTTIMOR", "OSTTIMOR"],
    "TG": ["TG", "TGO", "TOGO"],
    "TO": ["TO", "TON", "TONGA"],
    "TT": ["TT", "TTO", "TRINIDADANDTOBAGO"],
    "TN": ["TN", "TUN", "TUNISIA", "TUNESIEN"],
    "TR": ["TR", "TUR", "TURKEY", "TURKIYE", "TUERKEI", "TURKEI"],
    "TM": ["TM", "TKM", "TURKMENISTAN", "TURKMENIEN"],
    "TV": ["TV", "TUV", "TUVALU"],
    "UG": ["UG", "UGA", "UGANDA"],
    "UA": ["UA", "UKR", "UKRAINE"],
    "AE": ["AE", "ARE", "UAE", "UNITEDARABEMIRATES", "VEREINIGTEARABISCHEEMIRATE"],
    "GB": ["GB", "GBR", "UK", "UNITEDKINGDOM", "GREATBRITAIN", "BRITAIN", "ENGLAND", "SCOTLAND", "WALES", "NORTHERNIRELAND", "VEREINIGTESKOENIGREICH"],
    "US": ["US", "USA", "USAA", "UNITEDSTATES", "UNITEDSTATESOFAMERICA", "AMERICA", "VEREINIGTESTAATEN", "VEREINIGTESTAATENVONAMERIKA"],
    "UY": ["UY", "URY", "URUGUAY"],
    "UZ": ["UZ", "UZB", "UZBEKISTAN", "USBEKISTAN"],
    "VU": ["VU", "VUT", "VANUATU"],
    "VA": ["VA", "VAT", "VATICAN", "VATICANCITY", "HOLYSEE", "VATIKAN"],
    "VE": ["VE", "VEN", "VENEZUELA"],
    "VN": ["VN", "VNM", "VIETNAM"],
    "YE": ["YE", "YEM", "YEMEN"],
    "ZM": ["ZM", "ZMB", "ZAMBIA", "SAMBIA"],
    "ZW": ["ZW", "ZWE", "ZIMBABWE"],
}

country_lookup = {}
for iso_code, aliases in country_aliases.items():
    for alias in aliases:
        country_lookup[country_key(alias)] = iso_code

if "country" in df.columns:
    df["country"] = df["country"].map(
        lambda value: country_lookup.get(country_key(value), "UNKNOWN")
    ).astype("string")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)