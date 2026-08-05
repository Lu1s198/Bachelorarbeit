import os
import re
import unicodedata
import pandas as pd
import numpy as np

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/cleaning_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/cleaning_hard/output.parquet"

data = """
AF|AFG|Afghanistan
AL|ALB|Albania
DZ|DZA|Algeria
AS|ASM|American Samoa
AD|AND|Andorra
AO|AGO|Angola
AI|AIA|Anguilla
AQ|ATA|Antarctica
AG|ATG|Antigua and Barbuda
AR|ARG|Argentina
AM|ARM|Armenia
AW|ABW|Aruba
AU|AUS|Australia
AT|AUT|Austria
AZ|AZE|Azerbaijan
BS|BHS|Bahamas
BH|BHR|Bahrain
BD|BGD|Bangladesh
BB|BRB|Barbados
BY|BLR|Belarus
BE|BEL|Belgium
BZ|BLZ|Belize
BJ|BEN|Benin
BM|BMU|Bermuda
BT|BTN|Bhutan
BO|BOL|Bolivia
BQ|BES|Bonaire Sint Eustatius and Saba
BA|BIH|Bosnia and Herzegovina
BW|BWA|Botswana
BV|BVT|Bouvet Island
BR|BRA|Brazil
IO|IOT|British Indian Ocean Territory
BN|BRN|Brunei
BG|BGR|Bulgaria
BF|BFA|Burkina Faso
BI|BDI|Burundi
CV|CPV|Cabo Verde
KH|KHM|Cambodia
CM|CMR|Cameroon
CA|CAN|Canada
KY|CYM|Cayman Islands
CF|CAF|Central African Republic
TD|TCD|Chad
CL|CHL|Chile
CN|CHN|China
CX|CXR|Christmas Island
CC|CCK|Cocos Islands
CO|COL|Colombia
KM|COM|Comoros
CG|COG|Republic of the Congo
CD|COD|Democratic Republic of the Congo
CK|COK|Cook Islands
CR|CRI|Costa Rica
CI|CIV|Cote d Ivoire
HR|HRV|Croatia
CU|CUB|Cuba
CW|CUW|Curacao
CY|CYP|Cyprus
CZ|CZE|Czechia
DK|DNK|Denmark
DJ|DJI|Djibouti
DM|DMA|Dominica
DO|DOM|Dominican Republic
EC|ECU|Ecuador
EG|EGY|Egypt
SV|SLV|El Salvador
GQ|GNQ|Equatorial Guinea
ER|ERI|Eritrea
EE|EST|Estonia
SZ|SWZ|Eswatini
ET|ETH|Ethiopia
FK|FLK|Falkland Islands
FO|FRO|Faroe Islands
FJ|FJI|Fiji
FI|FIN|Finland
FR|FRA|France
GF|GUF|French Guiana
PF|PYF|French Polynesia
TF|ATF|French Southern Territories
GA|GAB|Gabon
GM|GMB|Gambia
GE|GEO|Georgia
DE|DEU|Germany
GH|GHA|Ghana
GI|GIB|Gibraltar
GR|GRC|Greece
GL|GRL|Greenland
GD|GRD|Grenada
GP|GLP|Guadeloupe
GU|GUM|Guam
GT|GTM|Guatemala
GG|GGY|Guernsey
GN|GIN|Guinea
GW|GNB|Guinea Bissau
GY|GUY|Guyana
HT|HTI|Haiti
HM|HMD|Heard Island and McDonald Islands
VA|VAT|Holy See
HN|HND|Honduras
HK|HKG|Hong Kong
HU|HUN|Hungary
IS|ISL|Iceland
IN|IND|India
ID|IDN|Indonesia
IR|IRN|Iran
IQ|IRQ|Iraq
IE|IRL|Ireland
IM|IMN|Isle of Man
IL|ISR|Israel
IT|ITA|Italy
JM|JAM|Jamaica
JP|JPN|Japan
JE|JEY|Jersey
JO|JOR|Jordan
KZ|KAZ|Kazakhstan
KE|KEN|Kenya
KI|KIR|Kiribati
KP|PRK|North Korea
KR|KOR|South Korea
KW|KWT|Kuwait
KG|KGZ|Kyrgyzstan
LA|LAO|Laos
LV|LVA|Latvia
LB|LBN|Lebanon
LS|LSO|Lesotho
LR|LBR|Liberia
LY|LBY|Libya
LI|LIE|Liechtenstein
LT|LTU|Lithuania
LU|LUX|Luxembourg
MO|MAC|Macao
MG|MDG|Madagascar
MW|MWI|Malawi
MY|MYS|Malaysia
MV|MDV|Maldives
ML|MLI|Mali
MT|MLT|Malta
MH|MHL|Marshall Islands
MQ|MTQ|Martinique
MR|MRT|Mauritania
MU|MUS|Mauritius
YT|MYT|Mayotte
MX|MEX|Mexico
FM|FSM|Micronesia
MD|MDA|Moldova
MC|MCO|Monaco
MN|MNG|Mongolia
ME|MNE|Montenegro
MS|MSR|Montserrat
MA|MAR|Morocco
MZ|MOZ|Mozambique
MM|MMR|Myanmar
NA|NAM|Namibia
NR|NRU|Nauru
NP|NPL|Nepal
NL|NLD|Netherlands
NC|NCL|New Caledonia
NZ|NZL|New Zealand
NI|NIC|Nicaragua
NE|NER|Niger
NG|NGA|Nigeria
NU|NIU|Niue
NF|NFK|Norfolk Island
MK|MKD|North Macedonia
MP|MNP|Northern Mariana Islands
NO|NOR|Norway
OM|OMN|Oman
PK|PAK|Pakistan
PW|PLW|Palau
PS|PSE|Palestine
PA|PAN|Panama
PG|PNG|Papua New Guinea
PY|PRY|Paraguay
PE|PER|Peru
PH|PHL|Philippines
PN|PCN|Pitcairn
PL|POL|Poland
PT|PRT|Portugal
PR|PRI|Puerto Rico
QA|QAT|Qatar
RE|REU|Reunion
RO|ROU|Romania
RU|RUS|Russia
RW|RWA|Rwanda
BL|BLM|Saint Barthelemy
SH|SHN|Saint Helena
KN|KNA|Saint Kitts and Nevis
LC|LCA|Saint Lucia
MF|MAF|Saint Martin
PM|SPM|Saint Pierre and Miquelon
VC|VCT|Saint Vincent and the Grenadines
WS|WSM|Samoa
SM|SMR|San Marino
ST|STP|Sao Tome and Principe
SA|SAU|Saudi Arabia
SN|SEN|Senegal
RS|SRB|Serbia
SC|SYC|Seychelles
SL|SLE|Sierra Leone
SG|SGP|Singapore
SX|SXM|Sint Maarten
SK|SVK|Slovakia
SI|SVN|Slovenia
SB|SLB|Solomon Islands
SO|SOM|Somalia
ZA|ZAF|South Africa
GS|SGS|South Georgia and the South Sandwich Islands
SS|SSD|South Sudan
ES|ESP|Spain
LK|LKA|Sri Lanka
SD|SDN|Sudan
SR|SUR|Suriname
SJ|SJM|Svalbard and Jan Mayen
SE|SWE|Sweden
CH|CHE|Switzerland
SY|SYR|Syria
TW|TWN|Taiwan
TJ|TJK|Tajikistan
TZ|TZA|Tanzania
TH|THA|Thailand
TL|TLS|Timor Leste
TG|TGO|Togo
TK|TKL|Tokelau
TO|TON|Tonga
TT|TTO|Trinidad and Tobago
TN|TUN|Tunisia
TR|TUR|Turkey
TM|TKM|Turkmenistan
TC|TCA|Turks and Caicos Islands
TV|TUV|Tuvalu
UG|UGA|Uganda
UA|UKR|Ukraine
AE|ARE|United Arab Emirates
GB|GBR|United Kingdom
US|USA|United States
UM|UMI|United States Minor Outlying Islands
UY|URY|Uruguay
UZ|UZB|Uzbekistan
VU|VUT|Vanuatu
VE|VEN|Venezuela
VN|VNM|Vietnam
VG|VGB|British Virgin Islands
VI|VIR|United States Virgin Islands
WF|WLF|Wallis and Futuna
EH|ESH|Western Sahara
YE|YEM|Yemen
ZM|ZMB|Zambia
ZW|ZWE|Zimbabwe
"""

aliases = {
    "AF": ["afghanistan"],
    "AL": ["albanien"],
    "DZ": ["algerien"],
    "AS": ["amerikanisch samoa"],
    "AD": ["andorra"],
    "AO": ["angola"],
    "AI": ["anguilla"],
    "AG": ["antigua und barbuda", "antigua"],
    "AR": ["argentinien"],
    "AM": ["armenien"],
    "AW": ["aruba"],
    "AU": ["australien", "aus"],
    "AT": ["osterreich", "austria"],
    "AZ": ["aserbaidschan"],
    "BS": ["the bahamas", "bahamas"],
    "BH": ["bahrain"],
    "BD": ["bangladesch"],
    "BB": ["barbados"],
    "BY": ["weissrussland", "belarus"],
    "BE": ["belgien"],
    "BZ": ["belize"],
    "BJ": ["benin"],
    "BM": ["bermuda"],
    "BT": ["bhutan"],
    "BO": ["bolivien", "plurinational state of bolivia"],
    "BA": ["bosnien und herzegowina", "bosnia"],
    "BW": ["botswana"],
    "BR": ["brasilien", "brasil"],
    "BN": ["brunei darussalam"],
    "BG": ["bulgarien"],
    "BF": ["burkina faso"],
    "BI": ["burundi"],
    "CV": ["cape verde", "kap verde", "cabo verde"],
    "KH": ["kambodscha"],
    "CM": ["kamerun"],
    "CA": ["kanada"],
    "KY": ["caymaninseln", "cayman islands"],
    "CF": ["zentralafrikanische republik"],
    "TD": ["tschad"],
    "CL": ["chile"],
    "CN": ["china", "prc", "people's republic of china"],
    "CO": ["kolumbien"],
    "KM": ["komoren"],
    "CG": ["congo brazzaville", "republic of congo", "republik kongo"],
    "CD": ["dr congo", "drc", "congo kinshasa", "democratic republic of congo", "demokratische republik kongo"],
    "CR": ["costa rica"],
    "CI": ["cote divoire", "ivory coast", "elfenbeinkuste", "elfenbeinkueste"],
    "HR": ["kroatien"],
    "CU": ["kuba"],
    "CW": ["curacao", "curaçao"],
    "CY": ["zypern"],
    "CZ": ["czech republic", "tschechien", "tschechische republik"],
    "DK": ["danemark"],
    "DO": ["dominikanische republik"],
    "EC": ["ecuador"],
    "EG": ["agypten", "aegypten"],
    "SV": ["el salvador"],
    "GQ": ["aquatorialguinea"],
    "ER": ["eritrea"],
    "EE": ["estland"],
    "SZ": ["swaziland", "eswatini"],
    "ET": ["athiopien", "aethiopien"],
    "FK": ["falklandinseln", "falkland islands"],
    "FO": ["faröer", "faroe islands", "faröer inseln"],
    "FJ": ["fidschi"],
    "FI": ["finnland"],
    "FR": ["frankreich"],
    "GF": ["franzosisch guayana", "franzoesisch guayana"],
    "PF": ["franzosisch polynesien", "franzoesisch polynesien"],
    "GA": ["gabun"],
    "GM": ["the gambia", "gambia"],
    "GE": ["georgien"],
    "DE": ["deutschland", "germany", "ger", "deu", "bundesrepublik deutschland", "deutsch"],
    "GH": ["ghana"],
    "GR": ["griechenland"],
    "GL": ["gronland", "groenland"],
    "GP": ["guadeloupe"],
    "GT": ["guatemala"],
    "GN": ["guinea"],
    "GW": ["guinea bissau"],
    "GY": ["guyana"],
    "HT": ["haiti"],
    "VA": ["vatican", "vatican city", "vatikan", "heiliger stuhl"],
    "HN": ["honduras"],
    "HK": ["hongkong"],
    "HU": ["ungarn"],
    "IS": ["island"],
    "IN": ["indien", "bharat"],
    "ID": ["indonesien"],
    "IR": ["iran", "islamic republic of iran"],
    "IQ": ["irak"],
    "IE": ["irland", "republic of ireland"],
    "IL": ["israel"],
    "IT": ["italien"],
    "JM": ["jamaika"],
    "JP": ["japan", "nippon"],
    "JO": ["jordanien"],
    "KZ": ["kasachstan"],
    "KE": ["kenia"],
    "KP": ["dprk", "north korea", "nordkorea", "democratic peoples republic of korea"],
    "KR": ["rok", "republic of korea", "south korea", "sudkorea", "suedkorea"],
    "KW": ["kuwait"],
    "KG": ["kirgisistan", "kyrgyz republic"],
    "LA": ["laos", "lao pdr"],
    "LV": ["lettland"],
    "LB": ["libanon"],
    "LS": ["lesotho"],
    "LR": ["liberia"],
    "LY": ["libyen"],
    "LI": ["liechtenstein"],
    "LT": ["litauen"],
    "LU": ["luxemburg"],
    "MO": ["macau", "macao"],
    "MG": ["madagaskar"],
    "MW": ["malawi"],
    "MY": ["malaysia"],
    "MV": ["malediven"],
    "ML": ["mali"],
    "MT": ["malta"],
    "MR": ["mauretanien"],
    "MU": ["mauritius"],
    "MX": ["mexiko"],
    "FM": ["federated states of micronesia"],
    "MD": ["moldawien", "republik moldau", "republic of moldova"],
    "MC": ["monaco"],
    "MN": ["mongolei"],
    "ME": ["montenegro"],
    "MA": ["marokko"],
    "MZ": ["mosambik"],
    "MM": ["burma", "myanmar"],
    "NA": ["namibia"],
    "NP": ["nepal"],
    "NL": ["niederlande", "holland", "the netherlands"],
    "NZ": ["neuseeland"],
    "NI": ["nicaragua"],
    "NE": ["niger"],
    "NG": ["nigeria"],
    "MK": ["mazedonien", "nordmazedonien", "republic of north macedonia"],
    "NO": ["norwegen"],
    "OM": ["oman"],
    "PK": ["pakistan"],
    "PS": ["palestinian territories", "palastina", "palaestina", "state of palestine"],
    "PA": ["panama"],
    "PG": ["papua neuguinea"],
    "PY": ["paraguay"],
    "PE": ["peru"],
    "PH": ["philippinen"],
    "PL": ["polen"],
    "PT": ["portugal"],
    "PR": ["puerto rico"],
    "QA": ["katar", "qatar"],
    "RO": ["rumanien", "romania"],
    "RU": ["russland", "russia", "russian federation"],
    "RW": ["ruanda"],
    "KN": ["st kitts and nevis", "saint kitts"],
    "LC": ["st lucia", "saint lucia"],
    "VC": ["st vincent and the grenadines", "saint vincent"],
    "WS": ["samoa"],
    "ST": ["sao tome", "sao tome and principe"],
    "SA": ["saudi arabien", "saudi arabia", "ksa"],
    "SN": ["senegal"],
    "RS": ["serbien"],
    "SC": ["seychellen"],
    "SL": ["sierra leone"],
    "SG": ["singapur"],
    "SK": ["slowakei"],
    "SI": ["slowenien"],
    "SB": ["solomon islands", "salomonen"],
    "SO": ["somalia"],
    "ZA": ["sudafrika", "suedafrika", "south africa", "rsa"],
    "SS": ["sudsudan", "suedsudan", "south sudan"],
    "ES": ["spanien"],
    "LK": ["sri lanka", "ceylon"],
    "SD": ["sudan"],
    "SR": ["suriname"],
    "SE": ["schweden"],
    "CH": ["schweiz", "switzerland", "suisse", "svizzera"],
    "SY": ["syrien"],
    "TW": ["taiwan", "republic of china"],
    "TJ": ["tadschikistan"],
    "TZ": ["tansania", "united republic of tanzania"],
    "TH": ["thailand", "thailandia"],
    "TL": ["east timor", "timor leste", "timor-leste", "osttimor"],
    "TG": ["togo"],
    "TO": ["tonga"],
    "TT": ["trinidad und tobago"],
    "TN": ["tunesien"],
    "TR": ["turkei", "tuerkei", "turkiye", "türkiye"],
    "TM": ["turkmenistan"],
    "UG": ["uganda"],
    "UA": ["ukraine"],
    "AE": ["uae", "vereinigte arabische emirate", "united arab emirates"],
    "GB": ["uk", "u k", "great britain", "britannien", "grossbritannien", "großbritannien", "united kingdom", "england", "scotland", "wales", "northern ireland"],
    "US": ["usa", "u s a", "us", "u s", "united states of america", "vereinigte staaten", "amerika", "america"],
    "UY": ["uruguay"],
    "UZ": ["usbekistan"],
    "VU": ["vanuatu"],
    "VE": ["venezuela", "venezuela bolivarian republic of"],
    "VN": ["vietnam", "viet nam"],
    "VG": ["british virgin islands", "britische jungferninseln"],
    "VI": ["us virgin islands", "united states virgin islands", "amerikanische jungferninseln"],
    "EH": ["westsahara", "western sahara"],
    "YE": ["jemen", "yemen"],
    "ZM": ["sambia"],
    "ZW": ["simbabwe", "zimbabwe"],
}

def normalize(value):
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.casefold().replace("&", " and ")
    text = re.sub(r"[\W_]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()

country_map = {}
for line in data.strip().splitlines():
    iso2, iso3, english_name = [part.strip() for part in line.split("|", 2)]
    for value in (iso2, iso3, english_name):
        key = normalize(value)
        if key:
            country_map[key] = iso2

for iso2, values in aliases.items():
    for value in values:
        key = normalize(value)
        if key:
            country_map[key] = iso2

df = pd.read_parquet(input_path)

for required_column in ["customer_id", "full_name", "email", "country", "registered_at"]:
    if required_column not in df.columns:
        df[required_column] = pd.NA

df["country"] = df["country"].map(lambda x: country_map.get(normalize(x), "UNKNOWN")).astype("string")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)