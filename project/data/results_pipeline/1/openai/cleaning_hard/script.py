import os
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/cleaning_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/cleaning_hard/output.parquet"

country_data = """
AF|AFG|Afghanistan|Islamische Republik Afghanistan
AL|ALB|Albania|Albanien
DZ|DZA|Algeria|Algerien
AS|ASM|American Samoa|Amerikanisch Samoa
AD|AND|Andorra
AO|AGO|Angola
AI|AIA|Anguilla
AQ|ATA|Antarctica|Antarktis
AG|ATG|Antigua and Barbuda|Antigua und Barbuda
AR|ARG|Argentina|Argentinien
AM|ARM|Armenia|Armenien
AW|ABW|Aruba
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
BJ|BEN|Benin|Bénin
BM|BMU|Bermuda
BT|BTN|Bhutan|Bhutan
BO|BOL|Bolivia|Bolivien|Plurinational State of Bolivia
BQ|BES|Bonaire Sint Eustatius and Saba|Bonaire|Sint Eustatius|Saba|Caribbean Netherlands
BA|BIH|Bosnia and Herzegovina|Bosnia Herzegovina|Bosnien und Herzegowina|Bosnien Herzegovina
BW|BWA|Botswana
BV|BVT|Bouvet Island|Bouvetinsel
BR|BRA|Brazil|Brasilien
IO|IOT|British Indian Ocean Territory|Britisches Territorium im Indischen Ozean
BN|BRN|Brunei|Brunei Darussalam
BG|BGR|Bulgaria|Bulgarien
BF|BFA|Burkina Faso
BI|BDI|Burundi
CV|CPV|Cape Verde|Cabo Verde|Kap Verde
KH|KHM|Cambodia|Kambodscha
CM|CMR|Cameroon|Kamerun
CA|CAN|Canada|Kanada
KY|CYM|Cayman Islands|Kaimaninseln
CF|CAF|Central African Republic|Central African Republic|Zentralafrikanische Republik
TD|TCD|Chad|Tschad
CL|CHL|Chile
CN|CHN|China|People's Republic of China|Volksrepublik China
CX|CXR|Christmas Island|Weihnachtsinsel
CC|CCK|Cocos Islands|Cocos Keeling Islands|Kokosinseln|Keelinginseln
CO|COL|Colombia|Kolumbien
KM|COM|Comoros|Komoren
CD|COD|Democratic Republic of the Congo|DR Congo|D R Congo|DRC|Democratic Congo|Kongo Kinshasa|Demokratische Republik Kongo
CG|COG|Republic of the Congo|Congo Republic|Kongo Brazzaville|Republik Kongo
CK|COK|Cook Islands|Cookinseln
CR|CRI|Costa Rica|Costa Rica
CI|CIV|Cote d Ivoire|Côte d Ivoire|Ivory Coast|Elfenbeinkueste|Elfenbeinküste
HR|HRV|Croatia|Kroatien
CU|CUB|Cuba|Kuba
CW|CUW|Curacao|Curaçao
CY|CYP|Cyprus|Zypern
CZ|CZE|Czechia|Czech Republic|Tschechien|Tschechische Republik
DK|DNK|Denmark|Daenemark|Dänemark
DJ|DJI|Djibouti|Dschibuti
DM|DMA|Dominica|Dominica
DO|DOM|Dominican Republic|Dominikanische Republik
EC|ECU|Ecuador|Ecuador
EG|EGY|Egypt|Aegypten|Ägypten
SV|SLV|El Salvador|El Salvador
GQ|GNQ|Equatorial Guinea|Aequatorialguinea|Äquatorialguinea
ER|ERI|Eritrea|Eritrea
EE|EST|Estonia|Estland
SZ|SWZ|Eswatini|Swaziland|Swasiland
ET|ETH|Ethiopia|Aethiopien|Äthiopien
FK|FLK|Falkland Islands|Falklandinseln|Malvinas
FO|FRO|Faroe Islands|Faeroe Islands|Färöer|Faroer Inseln
FJ|FJI|Fiji|Fidschi
FI|FIN|Finland|Finnland
FR|FRA|France|Frankreich
GF|GUF|French Guiana|Franzoesisch Guayana|Französisch Guayana
PF|PYF|French Polynesia|Franzoesisch Polynesien|Französisch Polynesien
TF|ATF|French Southern Territories|Franzoesische Sued und Antarktisgebiete|Französische Süd und Antarktisgebiete
GA|GAB|Gabon|Gabun
GM|GMB|Gambia|The Gambia
GE|GEO|Georgia|Georgien
DE|DEU|Germany|Deutschland|Federal Republic of Germany|Bundesrepublik Deutschland|German
GH|GHA|Ghana|Ghana
GI|GIB|Gibraltar|Gibraltar
GR|GRC|Greece|Griechenland|Hellas
GL|GRL|Greenland|Groenland|Grönland
GD|GRD|Grenada|Grenada
GP|GLP|Guadeloupe|Guadeloupe
GU|GUM|Guam|Guam
GT|GTM|Guatemala|Guatemala
GG|GGY|Guernsey|Guernsey
GN|GIN|Guinea|Guinea
GW|GNB|Guinea Bissau|Guinea-Bissau|Guinea Bissau
GY|GUY|Guyana|Guyana
HT|HTI|Haiti|Haiti
HM|HMD|Heard Island and McDonald Islands|Heard Island|McDonald Islands
VA|VAT|Holy See|Vatican City|Vatican|Vatikan|Vatikanstadt
HN|HND|Honduras|Honduras
HK|HKG|Hong Kong|Hongkong
HU|HUN|Hungary|Ungarn
IS|ISL|Iceland|Island|Island
IN|IND|India|Indien
ID|IDN|Indonesia|Indonesien
IR|IRN|Iran|Islamic Republic of Iran|Iran
IQ|IRQ|Iraq|Irak
IE|IRL|Ireland|Republic of Ireland|Irland
IM|IMN|Isle of Man|Man Island|Insel Man
IL|ISR|Israel|Israel
IT|ITA|Italy|Italien
JM|JAM|Jamaica|Jamaika
JP|JPN|Japan|Japan
JE|JEY|Jersey|Jersey
JO|JOR|Jordan|Jordanien
KZ|KAZ|Kazakhstan|Kasachstan
KE|KEN|Kenya|Kenia
KI|KIR|Kiribati|Kiribati
KP|PRK|North Korea|Democratic People's Republic of Korea|Nordkorea
KR|KOR|South Korea|Republic of Korea|Suedkorea|Südkorea
KW|KWT|Kuwait|Kuwait
KG|KGZ|Kyrgyzstan|Kirgisistan|Kirgistan
LA|LAO|Laos|Lao People's Democratic Republic|Laotische Volksdemokratische Republik
LV|LVA|Latvia|Lettland
LB|LBN|Lebanon|Libanon
LS|LSO|Lesotho|Lesotho
LR|LBR|Liberia|Liberia
LY|LBY|Libya|Libyen
LI|LIE|Liechtenstein|Liechtenstein
LT|LTU|Lithuania|Litauen
LU|LUX|Luxembourg|Luxemburg
MO|MAC|Macao|Macau
MG|MDG|Madagascar|Madagaskar
MW|MWI|Malawi|Malawi
MY|MYS|Malaysia|Malaysia
MV|MDV|Maldives|Malediven
ML|MLI|Mali|Mali
MT|MLT|Malta|Malta
MH|MHL|Marshall Islands|Marshallinseln
MQ|MTQ|Martinique|Martinique
MR|MRT|Mauritania|Mauretanien
MU|MUS|Mauritius|Mauritius
YT|MYT|Mayotte|Mayotte
MX|MEX|Mexico|Mexiko
FM|FSM|Micronesia|Federated States of Micronesia|Mikronesien
MD|MDA|Moldova|Republic of Moldova|Moldau|Republik Moldau
MC|MCO|Monaco|Monaco
MN|MNG|Mongolia|Mongolei
ME|MNE|Montenegro|Montenegro
MS|MSR|Montserrat|Montserrat
MA|MAR|Morocco|Marokko
MZ|MOZ|Mozambique|Mosambik
MM|MMR|Myanmar|Burma|Birma
NA|NAM|Namibia|Namibia
NR|NRU|Nauru|Nauru
NP|NPL|Nepal|Nepal
NL|NLD|Netherlands|The Netherlands|Holland|Niederlande
NC|NCL|New Caledonia|Neukaledonien
NZ|NZL|New Zealand|Neuseeland
NI|NIC|Nicaragua|Nicaragua
NE|NER|Niger|Niger
NG|NGA|Nigeria|Nigeria
NU|NIU|Niue|Niue
NF|NFK|Norfolk Island|Norfolkinsel
MK|MKD|North Macedonia|Macedonia|Mazedonien|Nordmazedonien
MP|MNP|Northern Mariana Islands|Nördliche Marianen
NO|NOR|Norway|Norwegen
OM|OMN|Oman|Oman
PK|PAK|Pakistan|Pakistan
PW|PLW|Palau|Palau
PS|PSE|Palestine|Palestinian Territories|State of Palestine|Palästina
PA|PAN|Panama|Panama
PG|PNG|Papua New Guinea|Papua Neuguinea
PY|PRY|Paraguay|Paraguay
PE|PER|Peru|Perú
PH|PHL|Philippines|Philippinen
PN|PCN|Pitcairn|Pitcairn Islands
PL|POL|Poland|Polen
PT|PRT|Portugal|Portugal
PR|PRI|Puerto Rico|Puerto Rico
QA|QAT|Qatar|Katar
RE|REU|Reunion|Réunion|Reunion
RO|ROU|Romania|Rumaenien|Rumänien
RU|RUS|Russia|Russian Federation|Russland|Russische Foederation|Russische Föderation
RW|RWA|Rwanda|Ruanda
BL|BLM|Saint Barthelemy|Saint Barthélemy|St Barthelemy
SH|SHN|Saint Helena|St Helena|Saint Helena Ascension and Tristan da Cunha
KN|KNA|Saint Kitts and Nevis|St Kitts and Nevis|St Kitts Nevis
LC|LCA|Saint Lucia|St Lucia
MF|MAF|Saint Martin|St Martin|Saint Martin French Part
PM|SPM|Saint Pierre and Miquelon|St Pierre and Miquelon
VC|VCT|Saint Vincent and the Grenadines|St Vincent and the Grenadines|St Vincent Grenadines
WS|WSM|Samoa|Samoa
SM|SMR|San Marino|San Marino
ST|STP|Sao Tome and Principe|São Tomé and Príncipe|Sao Tome Principe
SA|SAU|Saudi Arabia|Saudi Arabien
SN|SEN|Senegal|Senegal
RS|SRB|Serbia|Serbien
SC|SYC|Seychelles|Seychellen
SL|SLE|Sierra Leone|Sierra Leone
SG|SGP|Singapore|Singapur
SX|SXM|Sint Maarten|St Martin Dutch Part
SK|SVK|Slovakia|Slowakei
SI|SVN|Slovenia|Slowenien
SB|SLB|Solomon Islands|Salomoninseln
SO|SOM|Somalia|Somalia
ZA|ZAF|South Africa|Republic of South Africa|Suedafrika|Südafrika
GS|SGS|South Georgia and the South Sandwich Islands|South Georgia|South Sandwich Islands
SS|SSD|South Sudan|Sued Sudan|Südsudan
ES|ESP|Spain|Spanien
LK|LKA|Sri Lanka|Sri Lanka
SD|SDN|Sudan|Sudan
SR|SUR|Suriname|Surinam
SJ|SJM|Svalbard and Jan Mayen|Svalbard|Spitzbergen|Jan Mayen
SE|SWE|Sweden|Schweden
CH|CHE|Switzerland|Schweiz|Swiss
SY|SYR|Syria|Syrian Arab Republic|Syrien
TW|TWN|Taiwan|Taiwan Province of China
TJ|TJK|Tajikistan|Tadschikistan
TZ|TZA|Tanzania|United Republic of Tanzania|Tansania
TH|THA|Thailand|Thailand
TL|TLS|Timor Leste|East Timor|Osttimor
TG|TGO|Togo|Togo
TK|TKL|Tokelau|Tokelau
TO|TON|Tonga|Tonga
TT|TTO|Trinidad and Tobago|Trinidad und Tobago
TN|TUN|Tunisia|Tunesien
TR|TUR|Turkey|Türkiye|Turkiye|Tuerkei|Türkei
TM|TKM|Turkmenistan|Turkmenistan
TC|TCA|Turks and Caicos Islands|Turks Caicos Islands
TV|TUV|Tuvalu|Tuvalu
UG|UGA|Uganda|Uganda
UA|UKR|Ukraine|Ukraine
AE|ARE|United Arab Emirates|UAE|VAE|Vereinigte Arabische Emirate
GB|GBR|United Kingdom|UK|Great Britain|Britain|England|Scotland|Wales|Northern Ireland|Vereinigtes Koenigreich|Vereinigtes Königreich|Grossbritannien|Großbritannien
US|USA|United States|United States of America|US America|America|Vereinigte Staaten|Vereinigte Staaten von Amerika
UM|UMI|United States Minor Outlying Islands|US Minor Outlying Islands
UY|URY|Uruguay|Uruguay
UZ|UZB|Uzbekistan|Usbekistan
VU|VUT|Vanuatu|Vanuatu
VE|VEN|Venezuela|Venezuela Bolivarian Republic of
VN|VNM|Vietnam|Viet Nam|Vietnam
VG|VGB|British Virgin Islands|Virgin Islands British|Britische Jungferninseln
VI|VIR|US Virgin Islands|United States Virgin Islands|Virgin Islands US|Amerikanische Jungferninseln
WF|WLF|Wallis and Futuna|Wallis Futuna
EH|ESH|Western Sahara|Westsahara
YE|YEM|Yemen|Jemen
ZM|ZMB|Zambia|Sambia
ZW|ZWE|Zimbabwe|Simbabwe
XK|XKX|Kosovo
"""

def normalize_country(value):
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.casefold()
    return re.sub(r"[^a-z0-9]+", "", text)

country_map = {}
ambiguous = set()

for line in country_data.strip().splitlines():
    parts = [part.strip() for part in line.split("|") if part.strip()]
    code = parts[0]
    for alias in parts:
        key = normalize_country(alias)
        if not key:
            continue
        if key in country_map and country_map[key] != code:
            ambiguous.add(key)
        else:
            country_map[key] = code

for key in ambiguous:
    country_map[key] = "UNKNOWN"

df = pd.read_parquet(input_path)

normalized_country = df["country"].map(normalize_country)
df["country"] = normalized_country.map(country_map).fillna("UNKNOWN").astype("string")

Path(output_path).parent.mkdir(parents=True, exist_ok=True)
df.to_parquet(output_path, index=False)