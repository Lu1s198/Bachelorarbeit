import os
import re
import unicodedata
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r5/cleaning_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r5/cleaning_hard/output.parquet"

data = """AF|Afghanistan|Afghanistan
AL|Albania|Albanien
DZ|Algeria|Algerien
AD|Andorra|Andorra
AO|Angola|Angola
AG|Antigua and Barbuda|Antigua und Barbuda|Antigua
AR|Argentina|Argentinien
AM|Armenia|Armenien
AU|Australia|Australien
AT|Austria|Österreich|Oesterreich
AZ|Azerbaijan|Aserbaidschan
BS|Bahamas|Bahamas
BH|Bahrain|Bahrain
BD|Bangladesh|Bangladesch
BB|Barbados|Barbados
BY|Belarus|Weißrussland|Weissrussland
BE|Belgium|Belgien
BZ|Belize|Belize
BJ|Benin|Benin
BT|Bhutan|Bhutan
BO|Bolivia|Bolivien|Bolivia, Plurinational State of
BA|Bosnia and Herzegovina|Bosnien und Herzegowina|Bosnia Herzegovina
BW|Botswana|Botswana
BR|Brazil|Brasilien
BN|Brunei|Brunei Darussalam
BG|Bulgaria|Bulgarien
BF|Burkina Faso|Burkina Faso
BI|Burundi|Burundi
CV|Cabo Verde|Kap Verde|Cape Verde
KH|Cambodia|Kambodscha
CM|Cameroon|Kamerun
CA|Canada|Kanada
CF|Central African Republic|Zentralafrikanische Republik
TD|Chad|Tschad
CL|Chile|Chile
CN|China|China|People's Republic of China|PRC
CO|Colombia|Kolumbien
KM|Comoros|Komoren
CG|Republic of the Congo|Republik Kongo|Congo Brazzaville|Congo Republic
CD|Democratic Republic of the Congo|Demokratische Republik Kongo|DR Congo|DRC|Congo Kinshasa|Democratic Congo
CR|Costa Rica|Costa Rica
CI|Cote d'Ivoire|Elfenbeinküste|Ivory Coast|Côte d'Ivoire
HR|Croatia|Kroatien
CU|Cuba|Kuba
CY|Cyprus|Zypern
CZ|Czechia|Tschechien|Czech Republic
DK|Denmark|Dänemark
DJ|Djibouti|Dschibuti
DM|Dominica|Dominica
DO|Dominican Republic|Dominikanische Republik
EC|Ecuador|Ecuador
EG|Egypt|Ägypten|Aegypten
SV|El Salvador|El Salvador
GQ|Equatorial Guinea|Äquatorialguinea|Aequatorialguinea
ER|Eritrea|Eritrea
EE|Estonia|Estland
SZ|Eswatini|Swasiland
ET|Ethiopia|Äthiopien|Aethiopien
FJ|Fiji|Fidschi
FI|Finland|Finnland
FR|France|Frankreich
GA|Gabon|Gabun
GM|Gambia|Gambia
GE|Georgia|Georgien
DE|Germany|Deutschland|Federal Republic of Germany|Bundesrepublik Deutschland|GER
GH|Ghana|Ghana
GR|Greece|Griechenland|Hellas
GD|Grenada|Grenada
GT|Guatemala|Guatemala
GN|Guinea|Guinea
GW|Guinea-Bissau|Guinea Bissau
GY|Guyana|Guyana
HT|Haiti|Haiti
HN|Honduras|Honduras
HU|Hungary|Ungarn
IS|Iceland|Island
IN|India|Indien
ID|Indonesia|Indonesien
IR|Iran|Iran|Islamic Republic of Iran
IQ|Iraq|Irak
IE|Ireland|Irland
IL|Israel|Israel
IT|Italy|Italien
JM|Jamaica|Jamaika
JP|Japan|Japan
JO|Jordan|Jordanien
KZ|Kazakhstan|Kasachstan
KE|Kenya|Kenia
KI|Kiribati|Kiribati
KP|North Korea|Nordkorea|Democratic People's Republic of Korea|DPRK
KR|South Korea|Südkorea|Sudkorea|Republic of Korea|Korea South
KW|Kuwait|Kuwait
KG|Kyrgyzstan|Kirgisistan
LA|Laos|Laos|Lao People's Democratic Republic
LV|Latvia|Lettland
LB|Lebanon|Libanon
LS|Lesotho|Lesotho
LR|Liberia|Liberia
LY|Libya|Libyen
LI|Liechtenstein|Liechtenstein
LT|Lithuania|Litauen
LU|Luxembourg|Luxemburg
MG|Madagascar|Madagaskar
MW|Malawi|Malawi
MY|Malaysia|Malaysia
MV|Maldives|Malediven
ML|Mali|Mali
MT|Malta|Malta
MH|Marshall Islands|Marshallinseln
MR|Mauritania|Mauretanien
MU|Mauritius|Mauritius
MX|Mexico|Mexiko|México
FM|Micronesia|Mikronesien|Federated States of Micronesia
MD|Moldova|Moldau|Republic of Moldova
MC|Monaco|Monaco
MN|Mongolia|Mongolei
ME|Montenegro|Montenegro
MA|Morocco|Marokko
MZ|Mozambique|Mosambik
MM|Myanmar|Myanmar|Burma|Birma
NA|Namibia|Namibia
NR|Nauru|Nauru
NP|Nepal|Nepal
NL|Netherlands|Niederlande|Holland|The Netherlands
NZ|New Zealand|Neuseeland
NI|Nicaragua|Nicaragua
NE|Niger|Niger
NG|Nigeria|Nigeria
MK|North Macedonia|Nordmazedonien|Macedonia|Mazedonien
NO|Norway|Norwegen
OM|Oman|Oman
PK|Pakistan|Pakistan
PW|Palau|Palau
PS|Palestine|Palästina|Palaestina|State of Palestine|Palestinian Territories
PA|Panama|Panama
PG|Papua New Guinea|Papua-Neuguinea
PY|Paraguay|Paraguay
PE|Peru|Peru|Perú
PH|Philippines|Philippinen
PL|Poland|Polen
PT|Portugal|Portugal
QA|Qatar|Katar
RO|Romania|Rumänien|Rumaenien
RU|Russia|Russland|Russian Federation
RW|Rwanda|Ruanda
KN|Saint Kitts and Nevis|St. Kitts and Nevis|St Kitts and Nevis
LC|Saint Lucia|St. Lucia|St Lucia
VC|Saint Vincent and the Grenadines|St. Vincent and the Grenadines|St Vincent and the Grenadines
WS|Samoa|Samoa
SM|San Marino|San Marino
ST|Sao Tome and Principe|São Tomé und Príncipe|Sao Tome und Principe
SA|Saudi Arabia|Saudi-Arabien|Saudi Arabien
SN|Senegal|Senegal
RS|Serbia|Serbien
SC|Seychelles|Seychellen
SL|Sierra Leone|Sierra Leone
SG|Singapore|Singapur
SK|Slovakia|Slowakei|Slovak Republic
SI|Slovenia|Slowenien
SB|Solomon Islands|Salomonen
SO|Somalia|Somalia
ZA|South Africa|Südafrika|Sudafrika|Republic of South Africa
SS|South Sudan|Südsudan|Sudsudan
ES|Spain|Spanien
LK|Sri Lanka|Sri Lanka
SD|Sudan|Sudan
SR|Suriname|Suriname
SE|Sweden|Schweden
CH|Switzerland|Schweiz|Swiss Confederation
SY|Syria|Syrien|Syrian Arab Republic
TW|Taiwan|Taiwan|Republic of China
TJ|Tajikistan|Tadschikistan
TZ|Tanzania|Tansania|United Republic of Tanzania
TH|Thailand|Thailand
TL|Timor-Leste|Osttimor|East Timor
TG|Togo|Togo
TO|Tonga|Tonga
TT|Trinidad and Tobago|Trinidad und Tobago
TN|Tunisia|Tunesien
TR|Turkey|Türkei|Tuerkei|Türkiye
TM|Turkmenistan|Turkmenistan
TV|Tuvalu|Tuvalu
UG|Uganda|Uganda
UA|Ukraine|Ukraine
AE|United Arab Emirates|Vereinigte Arabische Emirate|UAE|VAE
GB|United Kingdom|Vereinigtes Königreich|UK|U.K.|Great Britain|Britain|England|Scotland|Wales|Northern Ireland
US|United States|United States of America|USA|U.S.A.|US|U.S.|Amerika|Vereinigte Staaten
UY|Uruguay|Uruguay
UZ|Uzbekistan|Usbekistan
VU|Vanuatu|Vanuatu
VA|Vatican City|Vatikanstadt|Vatican|Holy See
VE|Venezuela|Venezuela|Venezuela, Bolivarian Republic of
VN|Vietnam|Viet Nam
YE|Yemen|Jemen
ZM|Zambia|Sambia
ZW|Zimbabwe|Simbabwe
AX|Aland Islands|Ålandinseln|Aland
AS|American Samoa|Amerikanisch-Samoa
AI|Anguilla|Anguilla
AQ|Antarctica|Antarktis
AW|Aruba|Aruba
BM|Bermuda|Bermuda
BQ|Bonaire, Sint Eustatius and Saba|Bonaire
BV|Bouvet Island|Bouvetinsel
IO|British Indian Ocean Territory|Britisches Territorium im Indischen Ozean
KY|Cayman Islands|Kaimaninseln
CX|Christmas Island|Weihnachtsinsel
CC|Cocos Islands|Kokosinseln|Cocos Keeling Islands
CK|Cook Islands|Cookinseln
CW|Curacao|Curaçao
FK|Falkland Islands|Falklandinseln|Malvinas
FO|Faroe Islands|Färöer|Faröer
GF|French Guiana|Französisch-Guayana
PF|French Polynesia|Französisch-Polynesien
TF|French Southern Territories|Französische Süd- und Antarktisgebiete
GI|Gibraltar|Gibraltar
GL|Greenland|Grönland|Groenland
GP|Guadeloupe|Guadeloupe
GU|Guam|Guam
GG|Guernsey|Guernsey
HK|Hong Kong|Hongkong
IM|Isle of Man|Man Island
JE|Jersey|Jersey
MO|Macao|Macau
MQ|Martinique|Martinique
YT|Mayotte|Mayotte
MS|Montserrat|Montserrat
NC|New Caledonia|Neukaledonien
NU|Niue|Niue
NF|Norfolk Island|Norfolkinsel
MP|Northern Mariana Islands|Nördliche Marianen
PN|Pitcairn|Pitcairninseln
PR|Puerto Rico|Puerto Rico
RE|Reunion|Réunion
BL|Saint Barthelemy|Saint-Barthélemy
SH|Saint Helena|St. Helena|Saint Helena, Ascension and Tristan da Cunha
MF|Saint Martin|Saint-Martin
PM|Saint Pierre and Miquelon|Saint-Pierre und Miquelon
SX|Sint Maarten|Sint Maarten
GS|South Georgia and the South Sandwich Islands|Südgeorgien und die Südlichen Sandwichinseln
SJ|Svalbard and Jan Mayen|Spitzbergen und Jan Mayen
TK|Tokelau|Tokelau
TC|Turks and Caicos Islands|Turks- und Caicosinseln
UM|United States Minor Outlying Islands|Amerikanische Überseeinseln
VG|British Virgin Islands|Britische Jungferninseln
VI|U.S. Virgin Islands|Amerikanische Jungferninseln|US Virgin Islands
WF|Wallis and Futuna|Wallis und Futuna
EH|Western Sahara|Westsahara"""

def normalize(value):
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.upper().replace("&", " AND ")
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()

alias_map = {}
ambiguous = set()

for line in data.splitlines():
    parts = [part.strip() for part in line.split("|") if part.strip()]
    code = parts[0]
    for alias in parts:
        key = normalize(alias)
        if not key:
            continue
        if key in alias_map and alias_map[key] != code:
            ambiguous.add(key)
        else:
            alias_map[key] = code

for key in ambiguous:
    alias_map.pop(key, None)

df = pd.read_parquet(input_path)
normalized_country = df["country"].map(normalize)
df["country"] = normalized_country.map(alias_map).fillna("UNKNOWN").astype("string")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)