import os
import re
import unicodedata
import pandas as pd
import numpy as np

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai/cleaning_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai/cleaning_hard/output.parquet"

def normalize_country_value(value):
    if pd.isna(value):
        return ""
    text = str(value).strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.upper().replace("&", " AND ")
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()

country_definitions = {
    "AF": "AFG AFGHANISTAN",
    "AL": "ALB ALBANIA ALBANIEN",
    "DZ": "DZA ALGERIA ALGERIEN",
    "AD": "AND ANDORRA",
    "AO": "AGO ANGOLA",
    "AG": "ATG ANTIGUA AND BARBUDA ANTIGUA BARBUDA",
    "AR": "ARG ARGENTINA ARGENTINIEN",
    "AM": "ARM ARMENIA ARMENIEN",
    "AU": "AUS AUSTRALIA AUSTRALIEN",
    "AT": "AUT AUSTRIA OSTERREICH OESTERREICH",
    "AZ": "AZE AZERBAIJAN ASERBAIDSCHAN",
    "BS": "BHS BAHAMAS THE BAHAMAS",
    "BH": "BHR BAHRAIN BAHREIN",
    "BD": "BGD BANGLADESH",
    "BB": "BRB BARBADOS",
    "BY": "BLR BELARUS WEISSRUSSLAND BELARUSSIEN",
    "BE": "BEL BELGIUM BELGIEN",
    "BZ": "BLZ BELIZE",
    "BJ": "BEN BENIN",
    "BT": "BTN BHUTAN",
    "BO": "BOL BOLIVIA PLURINATIONAL STATE OF",
    "BA": "BIH BOSNIA AND HERZEGOVINA BOSNIEN UND HERZEGOWINA",
    "BW": "BWA BOTSWANA",
    "BR": "BRA BRAZIL BRASILIEN",
    "BN": "BRN BRUNEI BRUNEI DARUSSALAM",
    "BG": "BGR BULGARIA BULGARIEN",
    "BF": "BFA BURKINA FASO",
    "BI": "BDI BURUNDI",
    "CV": "CPV CABO VERDE CAPE VERDE KAP VERDE",
    "KH": "KHM CAMBODIA KAMBODSCHA",
    "CM": "CMR CAMEROON KAMERUN",
    "CA": "CAN CANADA KANADA",
    "CF": "CAF CENTRAL AFRICAN REPUBLIC ZENTRALAFRIKANISCHE REPUBLIK",
    "TD": "TCD CHAD TSCHAD",
    "CL": "CHL CHILE",
    "CN": "CHN CHINA PEOPLE S REPUBLIC OF CHINA VOLKSREPUBLIK CHINA PRC",
    "CO": "COL COLOMBIA KOLUMBIEN",
    "KM": "COM COMOROS KOMOREN",
    "CD": "COD DEMOCRATIC REPUBLIC OF THE CONGO DEMOCRATIC REPUBLIC CONGO DR CONGO DRC KONGO KINSHASA",
    "CG": "COG REPUBLIC OF THE CONGO CONGO REPUBLIC KONGO BRAZZAVILLE",
    "CR": "CRI COSTA RICA",
    "CI": "CIV COTE D IVOIRE IVORY COAST ELFENBEINKUSTE ELBEINKUSTE",
    "HR": "HRV CROATIA KROATIEN",
    "CU": "CUB CUBA KUBA",
    "CY": "CYP CYPRUS ZYPERN",
    "CZ": "CZE CZECHIA CZECH REPUBLIC TSCHECHIEN TSCHECHISCHE REPUBLIK",
    "DK": "DNK DENMARK DANEMARK",
    "DJ": "DJI DJIBOUTI",
    "DM": "DMA DOMINICA",
    "DO": "DOM DOMINICAN REPUBLIC DOMINIKANISCHE REPUBLIK",
    "EC": "ECU ECUADOR EKUADOR",
    "EG": "EGY EGYPT AEGYPTEN",
    "SV": "SLV EL SALVADOR",
    "GQ": "GNQ EQUATORIAL GUINEA AQUATORIALGUINEA AEGUATORIALGUINEA",
    "ER": "ERI ERITREA",
    "EE": "EST ESTONIA ESTLAND",
    "SZ": "SWZ ESWATINI SWAZILAND",
    "ET": "ETH ETHIOPIA ATHIOPIEN",
    "FJ": "FJI FIJI",
    "FI": "FIN FINLAND FINNLAND",
    "FR": "FRA FRANCE FRANKREICH",
    "GA": "GAB GABON",
    "GM": "GMB GAMBIA THE GAMBIA",
    "GE": "GEO GEORGIA GEORGIEN",
    "DE": "DEU GER GERMANY DEUTSCHLAND FEDERAL REPUBLIC OF GERMANY BUNDESREPUBLIK DEUTSCHLAND",
    "GH": "GHA GHANA",
    "GR": "GRC GREECE GRIECHENLAND HELLAS",
    "GD": "GRD GRENADA",
    "GT": "GTM GUATEMALA",
    "GN": "GIN GUINEA GUINEE",
    "GW": "GNB GUINEA BISSAU",
    "GY": "GUY GUYANA",
    "HT": "HTI HAITI HAITI",
    "HN": "HND HONDURAS",
    "HU": "HUN HUNGARY UNGARN",
    "IS": "ISL ICELAND ISLAND",
    "IN": "IND INDIA INDIEN BHARAT",
    "ID": "IDN INDONESIA",
    "IR": "IRN IRAN ISLAMIC REPUBLIC OF IRAN",
    "IQ": "IRQ IRAQ",
    "IE": "IRL IRELAND IRLAND REPUBLIC OF IRELAND",
    "IL": "ISR ISRAEL",
    "IT": "ITA ITALY ITALIEN",
    "JM": "JAM JAMAICA JAMAIKA",
    "JP": "JPN JAPAN JAPAN",
    "JO": "JOR JORDAN JORDANIEN",
    "KZ": "KAZ KAZAKHSTAN KASACHSTAN",
    "KE": "KEN KENYA",
    "KI": "KIR KIRIBATI",
    "KP": "PRK NORTH KOREA DEMOCRATIC PEOPLE S REPUBLIC OF KOREA NORDKOREA",
    "KR": "KOR SOUTH KOREA REPUBLIC OF KOREA SUEDKOREA SUDKOREA",
    "KW": "KWT KUWAIT KUWEIT",
    "KG": "KGZ KYRGYZSTAN KIRGHIZISTAN",
    "LA": "LAO LAOS LAO PEOPLE S DEMOCRATIC REPUBLIC",
    "LV": "LVA LATVIA LETTLAND",
    "LB": "LBN LEBANON LIBANON",
    "LS": "LSO LESOTHO",
    "LR": "LBR LIBERIA",
    "LY": "LBY LIBYA LIBYEN",
    "LI": "LIE LIECHTENSTEIN",
    "LT": "LTU LITHUANIA LITAUEN",
    "LU": "LUX LUXEMBOURG LUXEMBURG",
    "MG": "MDG MADAGASCAR",
    "MW": "MWI MALAWI",
    "MY": "MYS MALAYSIA MALAYSIA",
    "MV": "MDV MALDIVES MALDIVIEN",
    "ML": "MLI MALI",
    "MT": "MLT MALTA",
    "MH": "MHL MARSHALL ISLANDS MARSHALLINSELN",
    "MR": "MRT MAURITANIA MAURETANIEN",
    "MU": "MUS MAURITIUS",
    "MX": "MEX MEXICO MEXIKO",
    "FM": "FSM MICRONESIA FEDERATED STATES OF MIKRONESIEN",
    "MD": "MDA MOLDOVA REPUBLIC OF MOLDOVA MOLDAWIEN",
    "MC": "MCO MONACO MONAKO",
    "MN": "MNG MONGOLIA MONGOLEI",
    "ME": "MNE MONTENEGRO",
    "MA": "MAR MOROCCO MAROKKO",
    "MZ": "MOZ MOZAMBIQUE MOSAMBIK",
    "MM": "MMR MYANMAR BURMA BIRMA",
    "NA": "NAM NAMIBIA",
    "NR": "NRU NAURU",
    "NP": "NPL NEPAL",
    "NL": "NLD NETHERLANDS THE NETHERLANDS HOLLAND NIEDERLANDE",
    "NZ": "NZL NEW ZEALAND NEUSEELAND",
    "NI": "NIC NICARAGUA",
    "NE": "NER NIGER",
    "NG": "NGA NIGERIA NIGERIA",
    "MK": "MKD NORTH MACEDONIA MACEDONIA NORDMAZEDONIEN",
    "NO": "NOR NORWAY NORWEGEN",
    "OM": "OMN OMAN",
    "PK": "PAK PAKISTAN",
    "PW": "PLW PALAU",
    "PA": "PAN PANAMA",
    "PG": "PNG PAPUA NEW GUINEA PAPUA NEUGUINEA",
    "PY": "PRY PARAGUAY",
    "PE": "PER PERU",
    "PH": "PHL PHILIPPINES PHILIPPINEN",
    "PL": "POL POLAND POLEN",
    "PT": "PRT PORTUGAL",
    "QA": "QAT QATAR KATAR",
    "RO": "ROU ROMANIA RUMAENIEN RUMANIEN",
    "RU": "RUS RUSSIAN FEDERATION RUSSIA RUSSLAND",
    "RW": "RWA RWANDA RUANDA",
    "KN": "KNA SAINT KITTS AND NEVIS ST KITTS AND NEVIS",
    "LC": "LCA SAINT LUCIA ST LUCIA",
    "VC": "VCT SAINT VINCENT AND THE GRENADINES ST VINCENT AND THE GRENADINES",
    "WS": "WSM SAMOA",
    "SM": "SMR SAN MARINO",
    "ST": "STP SAO TOME AND PRINCIPE SAO TOME PRINCIPE",
    "SA": "SAU SAUDI ARABIA SAUDI ARABIEN KSA",
    "SN": "SEN SENEGAL",
    "RS": "SRB SERBIA SERBIEN",
    "SC": "SYC SEYCHELLES SEYCHELLEN",
    "SL": "SLE SIERRA LEONE",
    "SG": "SGP SINGAPORE SINGAPUR",
    "SK": "SVK SLOVAKIA SLOVAKIA SLOWAKEI",
    "SI": "SVN SLOVENIA SLOWENIEN",
    "SB": "SLB SOLOMON ISLANDS SOLOMONINSELN",
    "SO": "SOM SOMALIA",
    "ZA": "ZAF SOUTH AFRICA REPUBLIC OF SOUTH AFRICA SUEDAFRIKA SUD AFRIKA RSA",
    "SS": "SSD SOUTH SUDAN SUEDSUDAN SUDSUDAN",
    "ES": "ESP SPAIN SPANIEN",
    "LK": "LKA SRI LANKA",
    "SD": "SDN SUDAN",
    "SR": "SUR SURINAME",
    "SE": "SWE SWEDEN SCHWEDEN",
    "CH": "CHE SWITZERLAND SCHWEIZ",
    "SY": "SYR SYRIA SYRIEN SYRIAN ARAB REPUBLIC",
    "TJ": "TJK TAJIKISTAN TADSCHIKISTAN",
    "TZ": "TZA TANZANIA UNITED REPUBLIC OF TANZANIA",
    "TH": "THA THAILAND",
    "TL": "TLS TIMOR LESTE EAST TIMOR OSTTIMOR",
    "TG": "TGO TOGO",
    "TO": "TON TONGA",
    "TT": "TTO TRINIDAD AND TOBAGO TRINIDAD TOBAGO",
    "TN": "TUN TUNISIA TUNESIEN",
    "TR": "TUR TURKEY TURKIYE TÜRKIYE TUE RKIYE TURKEI",
    "TM": "TKM TURKMENISTAN TURKMENISTAN",
    "TV": "TUV TUVALU",
    "UG": "UGA UGANDA",
    "UA": "UKR UKRAINE UKRAINE",
    "AE": "ARE UNITED ARAB EMIRATES UAE VEREINIGTE ARABISCHE EMIRATE VAE",
    "GB": "GBR UNITED KINGDOM UK GREAT BRITAIN BRITAIN ENGLAND VEREINIGTES KONIGREICH GROSSBRITANNIEN",
    "US": "USA UNITED STATES UNITED STATES OF AMERICA U S A U S UNITED STATES AMERICA VEREINIGTE STAATEN",
    "UY": "URY URUGUAY",
    "UZ": "UZB UZBEKISTAN USBEKISTAN",
    "VU": "VUT VANUATU",
    "VA": "VAT VATICAN VATICAN CITY HOLY SEE VATIKAN VATIKANSTADT",
    "VE": "VEN VENEZUELA BOLIVARIAN REPUBLIC OF VENEZUELA",
    "VN": "VNM VIETNAM VIET NAM",
    "YE": "YEM YEMEN JEMEN",
    "ZM": "ZMB ZAMBIA SAMBIA",
    "ZW": "ZWE ZIMBABWE SIMBABWE",
    "TW": "TWN TAIWAN",
    "HK": "HKG HONG KONG",
    "MO": "MAC MACAO MACAU",
    "PS": "PSE PALESTINE STATE OF PALESTINE PALESTINIAN TERRITORIES",
    "PR": "PRI PUERTO RICO",
    "GU": "GUM GUAM",
    "VI": "VIR US VIRGIN ISLANDS UNITED STATES VIRGIN ISLANDS",
    "VG": "VGB BRITISH VIRGIN ISLANDS",
    "GF": "GUF FRENCH GUIANA FRANZOSISCH GUYANA",
    "PF": "PYF FRENCH POLYNESIA FRANZOSISCH POLYNESIEN",
    "RE": "REU REUNION",
    "GP": "GLP GUADELOUPE",
    "MQ": "MTQ MARTINIQUE",
    "NC": "NCL NEW CALEDONIA NEUKALEDONIEN",
    "AW": "ABW ARUBA",
    "CW": "CUW CURACAO",
    "SX": "SXM SINT MAARTEN",
    "BQ": "BES BONAIRE SINT EUSTATIUS AND SABA",
    "GL": "GRL GREENLAND GRONLAND",
    "FO": "FRO FAROE ISLANDS FAEROE ISLANDS FAROER INSELN",
    "GI": "GIB GIBRALTAR",
    "IM": "IMN ISLE OF MAN",
    "JE": "JEY JERSEY",
    "GG": "GGY GUERNSEY",
    "BM": "BMU BERMUDA",
    "KY": "CYM CAYMAN ISLANDS",
    "TC": "TCA TURKS AND CAICOS ISLANDS",
    "AI": "AIA ANGUILLA",
    "MS": "MSR MONTSERRAT",
    "FK": "FLK FALKLAND ISLANDS MALVINAS",
}

alias_to_codes = {}
for iso_code, aliases in country_definitions.items():
    for alias in aliases.split("|"):
        for token in alias.split("  "):
            normalized = normalize_country_value(token)
            if normalized:
                alias_to_codes.setdefault(normalized, set()).add(iso_code)

for iso_code, aliases in country_definitions.items():
    for alias in aliases.split():
        normalized = normalize_country_value(alias)
        if normalized and len(normalized) >= 2:
            alias_to_codes.setdefault(normalized, set()).add(iso_code)

for iso_code, aliases in country_definitions.items():
    normalized_full = normalize_country_value(aliases)
    if normalized_full:
        alias_to_codes.setdefault(normalized_full, set()).add(iso_code)

manual_aliases = {
    "GER": "DE", "D": "DE", "FEDERAL REPUBLIC GERMANY": "DE",
    "USA": "US", "US": "US", "U S": "US",
    "UK": "GB", "U K": "GB", "GB": "GB",
    "UAE": "AE", "VAE": "AE",
    "KSA": "SA",
    "PRC": "CN",
    "ROC": "TW",
}
for alias, iso_code in manual_aliases.items():
    alias_to_codes.setdefault(normalize_country_value(alias), set()).add(iso_code)

for iso_code, aliases in country_definitions.items():
    parts = aliases.split()
    for i in range(len(parts)):
        for j in range(i + 1, len(parts) + 1):
            phrase = normalize_country_value(" ".join(parts[i:j]))
            if len(phrase) >= 4:
                alias_to_codes.setdefault(phrase, set()).add(iso_code)

def resolve_country(value):
    normalized = normalize_country_value(value)
    if not normalized:
        return "UNKNOWN"
    candidates = alias_to_codes.get(normalized, set())
    if len(candidates) == 1:
        return next(iter(candidates))
    if normalized in country_definitions:
        return normalized
    return "UNKNOWN"

df = pd.read_parquet(input_path)
df["country"] = df["country"].map(resolve_country).astype("string")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)