import os
import re
import unicodedata
from io import StringIO

import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_isolated_r2/cleaning_hard/output.parquet"

country_data = """AD,AND,Andorra
AE,ARE,United Arab Emirates
AF,AFG,Afghanistan
AG,ATG,Antigua and Barbuda
AI,AIA,Anguilla
AL,ALB,Albania
AM,ARM,Armenia
AO,AGO,Angola
AQ,ATA,Antarctica
AR,ARG,Argentina
AS,ASM,American Samoa
AT,AUT,Austria
AU,AUS,Australia
AW,ABW,Aruba
AX,ALA,Aland Islands
AZ,AZE,Azerbaijan
BA,BIH,Bosnia and Herzegovina
BB,BRB,Barbados
BD,BGD,Bangladesh
BE,BEL,Belgium
BF,BFA,Burkina Faso
BG,BGR,Bulgaria
BH,BHR,Bahrain
BI,BDI,Burundi
BJ,BEN,Benin
BL,BLM,Saint Barthelemy
BM,BMU,Bermuda
BN,BRN,Brunei
BO,BOL,Bolivia
BQ,BES,Bonaire Sint Eustatius and Saba
BR,BRA,Brazil
BS,BHS,Bahamas
BT,BTN,Bhutan
BV,BVT,Bouvet Island
BW,BWA,Botswana
BY,BLR,Belarus
BZ,BLZ,Belize
CA,CAN,Canada
CC,CCK,Cocos Keeling Islands
CD,COD,Democratic Republic of the Congo
CF,CAF,Central African Republic
CG,COG,Republic of the Congo
CH,CHE,Switzerland
CI,CIV,Cote d Ivoire
CK,COK,Cook Islands
CL,CHL,Chile
CM,CMR,Cameroon
CN,CHN,China
CO,COL,Colombia
CR,CRI,Costa Rica
CU,CUB,Cuba
CV,CPV,Cabo Verde
CW,CUW,Curacao
CX,CXR,Christmas Island
CY,CYP,Cyprus
CZ,CZE,Czechia
DE,DEU,Germany
DJ,DJI,Djibouti
DK,DNK,Denmark
DM,DMA,Dominica
DO,DOM,Dominican Republic
DZ,DZA,Algeria
EC,ECU,Ecuador
EE,EST,Estonia
EG,EGY,Egypt
EH,ESH,Western Sahara
ER,ERI,Eritrea
ES,ESP,Spain
ET,ETH,Ethiopia
FI,FIN,Finland
FJ,FJI,Fiji
FK,FLK,Falkland Islands
FM,FSM,Micronesia
FO,FRO,Faroe Islands
FR,FRA,France
GA,GAB,Gabon
GB,GBR,United Kingdom
GD,GRD,Grenada
GE,GEO,Georgia
GF,GUF,French Guiana
GG,GGY,Guernsey
GH,GHA,Ghana
GI,GIB,Gibraltar
GL,GRL,Greenland
GM,GMB,Gambia
GN,GIN,Guinea
GP,GLP,Guadeloupe
GQ,GNQ,Equatorial Guinea
GR,GRC,Greece
GS,SGS,South Georgia and the South Sandwich Islands
GT,GTM,Guatemala
GU,GUM,Guam
GW,GNB,Guinea Bissau
GY,GUY,Guyana
HK,HKG,Hong Kong
HM,HMD,Heard Island and McDonald Islands
HN,HND,Honduras
HR,HRV,Croatia
HT,HTI,Haiti
HU,HUN,Hungary
ID,IDN,Indonesia
IE,IRL,Ireland
IL,ISR,Israel
IM,IMN,Isle of Man
IN,IND,India
IO,IOT,British Indian Ocean Territory
IQ,IRQ,Iraq
IR,IRN,Iran
IS,ISL,Iceland
IT,ITA,Italy
JE,JEY,Jersey
JM,JAM,Jamaica
JO,JOR,Jordan
JP,JPN,Japan
KE,KEN,Kenya
KG,KGZ,Kyrgyzstan
KH,KHM,Cambodia
KI,KIR,Kiribati
KM,COM,Comoros
KN,KNA,Saint Kitts and Nevis
KP,PRK,North Korea
KR,KOR,South Korea
KW,KWT,Kuwait
KY,CYM,Cayman Islands
KZ,KAZ,Kazakhstan
LA,LAO,Laos
LB,LBN,Lebanon
LC,LCA,Saint Lucia
LI,LIE,Liechtenstein
LK,LKA,Sri Lanka
LR,LBR,Liberia
LS,LSO,Lesotho
LT,LTU,Lithuania
LU,LUX,Luxembourg
LV,LVA,Latvia
LY,LBY,Libya
MA,MAR,Morocco
MC,MCO,Monaco
MD,MDA,Moldova
ME,MNE,Montenegro
MF,MAF,Saint Martin
MG,MDG,Madagascar
MH,MHL,Marshall Islands
MK,MKD,North Macedonia
ML,MLI,Mali
MM,MMR,Myanmar
MN,MNG,Mongolia
MO,MAC,Macao
MP,MNP,Northern Mariana Islands
MQ,MTQ,Martinique
MR,MRT,Mauritania
MS,MSR,Montserrat
MT,MLT,Malta
MU,MUS,Mauritius
MV,MDV,Maldives
MW,MWI,Malawi
MX,MEX,Mexico
MY,MYS,Malaysia
MZ,MOZ,Mozambique
NA,NAM,Namibia
NC,NCL,New Caledonia
NE,NER,Niger
NF,NFK,Norfolk Island
NG,NGA,Nigeria
NI,NIC,Nicaragua
NL,NLD,Netherlands
NO,NOR,Norway
NP,NPL,Nepal
NR,NRU,Nauru
NU,NIU,Niue
NZ,NZL,New Zealand
OM,OMN,Oman
PA,PAN,Panama
PE,PER,Peru
PF,PYF,French Polynesia
PG,PNG,Papua New Guinea
PH,PHL,Philippines
PK,PAK,Pakistan
PL,POL,Poland
PM,SPM,Saint Pierre and Miquelon
PN,PCN,Pitcairn
PR,PRI,Puerto Rico
PS,PSE,Palestine
PT,PRT,Portugal
PW,PLW,Palau
PY,PRY,Paraguay
QA,QAT,Qatar
RE,REU,Reunion
RO,ROU,Romania
RS,SRB,Serbia
RU,RUS,Russia
RW,RWA,Rwanda
SA,SAU,Saudi Arabia
SB,SLB,Solomon Islands
SC,SYC,Seychelles
SD,SDN,Sudan
SE,SWE,Sweden
SG,SGP,Singapore
SH,SHN,Saint Helena
SI,SVN,Slovenia
SJ,SJM,Svalbard and Jan Mayen
SK,SVK,Slovakia
SL,SLE,Sierra Leone
SM,SMR,San Marino
SN,SEN,Senegal
SO,SOM,Somalia
SR,SUR,Suriname
SS,SSD,South Sudan
ST,STP,Sao Tome and Principe
SV,SLV,El Salvador
SX,SXM,Sint Maarten
SY,SYR,Syria
SZ,SWZ,Eswatini
TC,TCA,Turks and Caicos Islands
TD,TCD,Chad
TF,ATF,French Southern Territories
TG,TGO,Togo
TH,THA,Thailand
TJ,TJK,Tajikistan
TK,TKL,Tokelau
TL,TLS,Timor Leste
TM,TKM,Turkmenistan
TN,TUN,Tunisia
TO,TON,Tonga
TR,TUR,Turkey
TT,TTO,Trinidad and Tobago
TV,TUV,Tuvalu
TW,TWN,Taiwan
TZ,TZA,Tanzania
UA,UKR,Ukraine
UG,UGA,Uganda
UM,UMI,United States Minor Outlying Islands
US,USA,United States
UY,URY,Uruguay
UZ,UZB,Uzbekistan
VA,VAT,Vatican City
VC,VCT,Saint Vincent and the Grenadines
VE,VEN,Venezuela
VG,VGB,British Virgin Islands
VI,VIR,United States Virgin Islands
VN,VNM,Vietnam
VU,VUT,Vanuatu
WF,WLF,Wallis and Futuna
WS,WSM,Samoa
YE,YEM,Yemen
YT,MYT,Mayotte
ZA,ZAF,South Africa
ZM,ZMB,Zambia
ZW,ZWE,Zimbabwe
"""

def normalize(value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.casefold().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()

mapping = {}
for line in country_data.strip().splitlines():
    code, alpha3, name = line.split(",", 2)
    mapping[normalize(code)] = code
    mapping[normalize(alpha3)] = code
    mapping[normalize(name)] = code

aliases = {
    "deutschland": "DE", "bundesrepublik deutschland": "DE", "ger": "DE",
    "osterreich": "AT", "oesterreich": "AT", "schweiz": "CH", "suisse": "CH",
    "frankreich": "FR", "france": "FR", "italien": "IT", "spanien": "ES",
    "portugal": "PT", "niederlande": "NL", "holland": "NL",
    "belgien": "BE", "luxemburg": "LU", "danemark": "DK", "schweden": "SE",
    "norwegen": "NO", "finnland": "FI", "island": "IS", "irland": "IE",
    "grossbritannien": "GB", "großbritannien": "GB", "vereinigtes konigreich": "GB",
    "vereinigtes königreich": "GB", "england": "GB", "scotland": "GB",
    "wales": "GB", "nordirland": "GB", "uk": "GB", "u k": "GB", "great britain": "GB",
    "tschechien": "CZ", "czech republic": "CZ", "slowakei": "SK",
    "slowenien": "SI", "kroatien": "HR", "bosnien und herzegowina": "BA",
    "serbien": "RS", "montenegro": "ME", "nordmazedonien": "MK",
    "mazedonien": "MK", "albanien": "AL", "griechenland": "GR",
    "bulgarien": "BG", "rumanien": "RO", "rumänien": "RO", "ungarn": "HU",
    "polen": "PL", "estland": "EE", "lettland": "LV", "litauen": "LT",
    "ukraine": "UA", "weissrussland": "BY", "weißrussland": "BY",
    "russland": "RU", "russian federation": "RU", "turkei": "TR", "türkei": "TR",
    "zypern": "CY", "malta": "MT", "usa": "US", "u s a": "US",
    "us": "US", "u s": "US", "united states of america": "US",
    "amerika": "US", "vereinigte staaten": "US", "kanada": "CA",
    "mexiko": "MX", "brasilien": "BR", "argentinien": "AR", "chile": "CL",
    "kolumbien": "CO", "peru": "PE", "bolivien": "BO", "ecuador": "EC",
    "venezuela": "VE", "uruguay": "UY", "paraguay": "PY", "guyana": "GY",
    "surinam": "SR", "costa rica": "CR", "panama": "PA", "guatemala": "GT",
    "honduras": "HN", "nicaragua": "NI", "el salvador": "SV",
    "dominikanische republik": "DO", "kuba": "CU", "jamaika": "JM",
    "bahamas": "BS", "china": "CN", "volksrepublik china": "CN",
    "pr china": "CN", "taiwan": "TW", "republik china": "TW",
    "japan": "JP", "sudkorea": "KR", "sud korea": "KR", "south korea": "KR",
    "republik korea": "KR", "nordkorea": "KP", "north korea": "KP",
    "demokratische volksrepublik korea": "KP", "indien": "IN",
    "indonesien": "ID", "malaysia": "MY", "singapur": "SG",
    "thailand": "TH", "vietnam": "VN", "viet nam": "VN", "philippinen": "PH",
    "kambodscha": "KH", "laos": "LA", "myanmar": "MM", "burma": "MM",
    "brunei darussalam": "BN", "osttimor": "TL", "timor leste": "TL",
    "australien": "AU", "neuseeland": "NZ", "papua neuguinea": "PG",
    "fidschi": "FJ", "vereinigte arabische emirate": "AE", "vae": "AE",
    "uae": "AE", "saudi arabien": "SA", "saudi arabia": "SA",
    "iran": "IR", "irak": "IQ", "israel": "IL", "palastina": "PS",
    "palästina": "PS", "jordanien": "JO", "libanon": "LB", "syrien": "SY",
    "jemen": "YE", "oman": "OM", "katar": "QA", "kuwait": "KW",
    "bahrain": "BH", "afghanistan": "AF", "pakistan": "PK",
    "bangladesch": "BD", "sri lanka": "LK", "nepal": "NP", "bhutan": "BT",
    "kasachstan": "KZ", "usbekistan": "UZ", "turkmenistan": "TM",
    "kirgisistan": "KG", "tadschikistan": "TJ", "georgien": "GE",
    "armenien": "AM", "aserbaidschan": "AZ", "moldawien": "MD",
    "moldova republic of": "MD", "marokko": "MA", "algerien": "DZ",
    "tunesien": "TN", "libyen": "LY", "agypten": "EG", "ägypten": "EG",
    "sudan": "SD", "sudsudan": "SS", "südsudan": "SS", "athiopien": "ET",
    "äthiopien": "ET", "somalia": "SO", "kenia": "KE", "uganda": "UG",
    "tansania": "TZ", "tanzania united republic of": "TZ", "ruanda": "RW",
    "burundi": "BI", "demokratische republik kongo": "CD",
    "democratic republic of congo": "CD", "dr congo": "CD", "drc": "CD",
    "republik kongo": "CG", "republic of congo": "CG", "kongo brazzaville": "CG",
    "nigeria": "NG", "ghana": "GH", "senegal": "SN", "elfenbeinkuste": "CI",
    "elfenbeinküste": "CI", "ivory coast": "CI", "cote divoire": "CI",
    "kamerun": "CM", "angola": "AO", "sambia": "ZM", "simbabwe": "ZW",
    "simbabwe": "ZW", "sudafrika": "ZA", "south africa": "ZA",
    "namibia": "NA", "botswana": "BW", "mosambik": "MZ", "madagaskar": "MG",
    "mauritius": "MU", "kap verde": "CV", "cape verde": "CV",
    "swaziland": "SZ", "vatican": "VA", "vatikan": "VA",
    "holy see": "VA", "kosovo": "XK", "xk": "XK"
}

for alias, code in aliases.items():
    mapping[normalize(alias)] = code

df = pd.read_parquet(input_path)

if "country" not in df.columns:
    df["country"] = "UNKNOWN"
else:
    normalized = df["country"].map(normalize)
    df["country"] = normalized.map(mapping).fillna("UNKNOWN").astype("str")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)