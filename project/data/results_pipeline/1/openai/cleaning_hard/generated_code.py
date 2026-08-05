import os
import re
import unicodedata
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/cleaning_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/cleaning_hard/output.parquet"

data = """
AF|AFG|Afghanistan
AL|ALB|Albania|Albanien
DZ|DZA|Algeria|Algerien
AD|AND|Andorra
AO|AGO|Angola
AG|ATG|Antigua and Barbuda|Antigua und Barbuda
AR|ARG|Argentina|Argentinien
AM|ARM|Armenia|Armenien
AU|AUS|Australia|Australien
AT|AUT|Austria|Oesterreich|Österreich
AZ|AZE|Azerbaijan|Aserbaidschan
BS|BHS|Bahamas|The Bahamas
BH|BHR|Bahrain|Bahrain
BD|BGD|Bangladesh|Bangladesch
BB|BRB|Barbados
BY|BLR|Belarus|Weissrussland|Weißrussland
BE|BEL|Belgium|Belgien
BZ|BLZ|Belize
BJ|BEN|Benin
BT|BTN|Bhutan|Bhutan
BO|BOL|Bolivia|Bolivien
BA|BIH|Bosnia and Herzegovina|Bosnia Herzegovina|Bosnien und Herzegowina|Bosnien-Herzegowina
BW|BWA|Botswana
BR|BRA|Brazil|Brasilien
BN|BRN|Brunei|Brunei Darussalam
BG|BGR|Bulgaria|Bulgarien
BF|BFA|Burkina Faso
BI|BDI|Burundi
CV|CPV|Cabo Verde|Cape Verde|Kap Verde
KH|KHM|Cambodia|Kambodscha
CM|CMR|Cameroon|Kamerun
CA|CAN|Canada|Kanada
CF|CAF|Central African Republic|Central African Rep|Zentralafrikanische Republik
TD|TCD|Chad|Tschad
CL|CHL|Chile
CN|CHN|China|People's Republic of China|Volksrepublik China
CO|COL|Colombia|Kolumbien
KM|COM|Comoros|Komoren
CD|COD|Democratic Republic of the Congo|DR Congo|DRC|Congo Kinshasa|Demokratische Republik Kongo|Kongo Kinshasa
CG|COG|Republic of the Congo|Congo Brazzaville|Republik Kongo|Kongo Brazzaville
CR|CRI|Costa Rica
CI|CIV|Cote d Ivoire|Côte d'Ivoire|Ivory Coast|Elfenbeinkueste|Elfenbeinküste
HR|HRV|Croatia|Kroatien
CU|CUB|Cuba|Kuba
CY|CYP|Cyprus|Zypern
CZ|CZE|Czechia|Czech Republic|Tschechien|Tschechische Republik
DK|DNK|Denmark|Daenemark|Dänemark
DJ|DJI|Djibouti|Dschibuti
DM|DMA|Dominica
DO|DOM|Dominican Republic|Dominikanische Republik
EC|ECU|Ecuador
EG|EGY|Egypt|Aegypten|Ägypten
SV|SLV|El Salvador
GQ|GNQ|Equatorial Guinea|Aequatorialguinea|Äquatorialguinea
ER|ERI|Eritrea
EE|EST|Estonia|Estland
SZ|SWZ|Eswatini|Swaziland
ET|ETH|Ethiopia|Aethiopien|Äthiopien
FJ|FJI|Fiji|Fidschi
FI|FIN|Finland|Finnland
FR|FRA|France|Frankreich
GA|GAB|Gabon
GM|GMB|Gambia|The Gambia
GE|GEO|Georgia|Georgien
DE|DEU|Germany|Deutschland|German|Germania|Bundesrepublik Deutschland|BRD
GH|GHA|Ghana
GR|GRC|Greece|Griechenland
GD|GRD|Grenada
GT|GTM|Guatemala
GN|GIN|Guinea
GW|GNB|Guinea Bissau|Guinea-Bissau
GY|GUY|Guyana
HT|HTI|Haiti|Haiti
HN|HND|Honduras
HU|HUN|Hungary|Ungarn
IS|ISL|Iceland|Island
IN|IND|India|Indien
ID|IDN|Indonesia|Indonesien
IR|IRN|Iran|Iran Islamic Republic of
IQ|IRQ|Iraq|Irak
IE|IRL|Ireland|Irland
IL|ISR|Israel
IT|ITA|Italy|Italien
JM|JAM|Jamaica|Jamaika
JP|JPN|Japan|Japon
JO|JOR|Jordan|Jordanien
KZ|KAZ|Kazakhstan|Kasachstan
KE|KEN|Kenya|Kenia
KI|KIR|Kiribati
KP|PRK|North Korea|Democratic People's Republic of Korea|Nordkorea|Korea North
KR|KOR|South Korea|Republic of Korea|Südkorea|Sudkorea|Korea South
KW|KWT|Kuwait
KG|KGZ|Kyrgyzstan|Kyrgyz Republic|Kirgisistan
LA|LAO|Laos|Lao People's Democratic Republic
LV|LVA|Latvia|Lettland
LB|LBN|Lebanon|Libanon
LS|LSO|Lesotho
LR|LBR|Liberia
LY|LBY|Libya|Libyen
LI|LIE|Liechtenstein
LT|LTU|Lithuania|Litauen
LU|LUX|Luxembourg|Luxemburg
MG|MDG|Madagascar|Madagaskar
MW|MWI|Malawi
MY|MYS|Malaysia|Malaysia
MV|MDV|Maldives|Malediven
ML|MLI|Mali
MT|MLT|Malta
MH|MHL|Marshall Islands|Marshallinseln
MR|MRT|Mauritania|Mauretanien
MU|MUS|Mauritius
MX|MEX|Mexico|Mexiko
FM|FSM|Micronesia|Federated States of Micronesia|Mikronesien
MD|MDA|Moldova|Republic of Moldova|Moldau
MC|MCO|Monaco|Monako
MN|MNG|Mongolia|Mongolei
ME|MNE|Montenegro
MA|MAR|Morocco|Marokko
MZ|MOZ|Mozambique|Mosambik
MM|MMR|Myanmar|Burma|Birma
NA|NAM|Namibia
NR|NRU|Nauru
NP|NPL|Nepal
NL|NLD|Netherlands|The Netherlands|Holland|Niederlande
NZ|NZL|New Zealand|Neuseeland
NI|NIC|Nicaragua
NE|NER|Niger
NG|NGA|Nigeria|Nigeria
MK|MKD|North Macedonia|Macedonia|Mazedonien|Nordmazedonien
NO|NOR|Norway|Norwegen
OM|OMN|Oman
PK|PAK|Pakistan
PW|PLW|Palau
PA|PAN|Panama|Panama
PG|PNG|Papua New Guinea|Papua-Neuguinea
PY|PRY|Paraguay
PE|PER|Peru|Perú
PH|PHL|Philippines|Philippinen
PL|POL|Poland|Polen
PT|PRT|Portugal
QA|QAT|Qatar|Katar
RO|ROU|Romania|Rumania|Rumänien
RU|RUS|Russia|Russian Federation|Russland
RW|RWA|Rwanda|Ruanda
KN|KNA|Saint Kitts and Nevis|St Kitts and Nevis|St. Kitts and Nevis
LC|LCA|Saint Lucia|St Lucia|St. Lucia
VC|VCT|Saint Vincent and the Grenadines|St Vincent and the Grenadines
WS|WSM|Samoa
SM|SMR|San Marino
ST|STP|Sao Tome and Principe|São Tomé and Príncipe
SA|SAU|Saudi Arabia|Saudi-Arabien|Saudi Arabien
SN|SEN|Senegal
RS|SRB|Serbia|Serbien
SC|SYC|Seychelles|Seychellen
SL|SLE|Sierra Leone
SG|SGP|Singapore|Singapur
SK|SVK|Slovakia|Slowakia|Slowakei
SI|SVN|Slovenia|Slowenien
SB|SLB|Solomon Islands|Salomonen
SO|SOM|Somalia
ZA|ZAF|South Africa|Republic of South Africa|Suedafrika|Südafrika
SS|SSD|South Sudan|Sued Sudan|Südsudan
ES|ESP|Spain|Spanien
LK|LKA|Sri Lanka
SD|SDN|Sudan|Sudan
SR|SUR|Suriname
SE|SWE|Sweden|Schweden
CH|CHE|Switzerland|Schweiz|Swiss
SY|SYR|Syria|Syrian Arab Republic|Syrien
TJ|TJK|Tajikistan|Tadschikistan
TZ|TZA|Tanzania|United Republic of Tanzania|Tansania
TH|THA|Thailand|Thailand
TL|TLS|Timor Leste|East Timor|Osttimor
TG|TGO|Togo
TO|TON|Tonga
TT|TTO|Trinidad and Tobago|Trinidad und Tobago
TN|TUN|Tunisia|Tunesien
TR|TUR|Turkey|Türkiye|Turkiye|Tuerkei|Türkei
TM|TKM|Turkmenistan|Turkmenistan
TV|TUV|Tuvalu
UG|UGA|Uganda|Uganda
UA|UKR|Ukraine|Ukraine
AE|ARE|United Arab Emirates|UAE|Vereinigte Arabische Emirate
GB|GBR|United Kingdom|UK|Great Britain|Britain|England|Scotland|Wales|Northern Ireland|Vereinigtes Koenigreich|Vereinigtes Königreich|Grossbritannien|Großbritannien
US|USA|United States|United States of America|USA|US|U S A|America|Vereinigte Staaten
UY|URY|Uruguay
UZ|UZB|Uzbekistan|Usbekistan
VU|VUT|Vanuatu
VA|VAT|Vatican City|Holy See|Vatican|Vatikan|Vatikanstadt
VE|VEN|Venezuela|Venezuela
VN|VNM|Vietnam|Viet Nam
YE|YEM|Yemen|Jemen
ZM|ZMB|Zambia|Sambia
ZW|ZWE|Zimbabwe|Simbabwe
TW|TWN|Taiwan|Taiwan China
HK|HKG|Hong Kong
MO|MAC|Macao|Macau
PS|PSE|Palestine|Palestinian Territories|State of Palestine|Palaestina|Palästina
PR|PRI|Puerto Rico
GU|GUM|Guam
VI|VIR|US Virgin Islands|United States Virgin Islands
VG|VGB|British Virgin Islands
BM|BMU|Bermuda
KY|CYM|Cayman Islands
GI|GIB|Gibraltar
GL|GRL|Greenland|Groenland|Grönland
FO|FRO|Faroe Islands|Faeroe Islands|Färöer
RE|REU|Reunion|Réunion
GF|GUF|French Guiana|Franzoesisch Guayana|Französisch-Guayana
PF|PYF|French Polynesia|Franzoesisch Polynesien|Französisch-Polynesien
NC|NCL|New Caledonia|Neukaledonien
MQ|MTQ|Martinique
GP|GLP|Guadeloupe
AW|ABW|Aruba
CW|CUW|Curacao|Curaçao
SX|SXM|Sint Maarten
BL|BLM|Saint Barthelemy|Saint Barthélemy
MF|MAF|Saint Martin
PM|SPM|Saint Pierre and Miquelon
YT|MYT|Mayotte
TF|ATF|French Southern Territories
IO|IOT|British Indian Ocean Territory
CC|CCK|Cocos Islands
CX|CXR|Christmas Island
NF|NFK|Norfolk Island
PN|PCN|Pitcairn
TK|TKL|Tokelau
WF|WLF|Wallis and Futuna
EH|ESH|Western Sahara|Westsahara
AQ|ATA|Antarctica|Antarktis
AX|ALA|Aland Islands|Åland Islands|Aland
BQ|BES|Bonaire Sint Eustatius and Saba|Caribbean Netherlands
IM|IMN|Isle of Man|Man Island
JE|JEY|Jersey
GG|GGY|Guernsey
"""

def normalize_country(value):
    if pd.isna(value):
        return ""
    text = str(value).strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace("ß", "ss").replace("ẞ", "SS")
    return re.sub(r"[^a-z0-9]+", "", text.lower())

country_map = {}
for line in data.strip().splitlines():
    parts = [part.strip() for part in line.split("|") if part.strip()]
    code = parts[0]
    for alias in parts:
        key = normalize_country(alias)
        if key:
            if key not in country_map:
                country_map[key] = code
            elif country_map[key] != code:
                country_map[key] = "UNKNOWN"

additional_aliases = {
    "d": "DE", "deutsch": "DE", "deutsche": "DE", "german": "DE",
    "f": "FR", "franzoesisch": "FR", "franzosisch": "FR",
    "i": "IT", "italienisch": "IT",
    "e": "ES", "spanisch": "ES",
    "nl": "NL", "holland": "NL",
    "ch": "CH", "schweizerisch": "CH",
    "at": "AT", "oesterreichisch": "AT", "österreichisch": "AT",
    "gb": "GB", "u k": "GB", "uk": "GB",
    "usa": "US", "u s": "US", "u s a": "US",
    "brasil": "BR", "br": "BR",
    "russische foederation": "RU", "russische föderation": "RU",
    "korea republic": "KR", "korea democratic peoples republic": "KP",
}
for alias, code in additional_aliases.items():
    country_map[normalize_country(alias)] = code

df = pd.read_parquet(input_path)

if "country" not in df.columns:
    df["country"] = "UNKNOWN"
else:
    normalized = df["country"].map(normalize_country)
    result = normalized.map(country_map)

    def resolve(value, mapped):
        if pd.notna(mapped):
            return mapped
        if not value:
            return "UNKNOWN"
        return "UNKNOWN"

    df["country"] = [resolve(value, mapped) for value, mapped in zip(normalized, result)]

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)