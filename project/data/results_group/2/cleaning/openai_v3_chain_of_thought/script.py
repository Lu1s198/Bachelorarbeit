import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# Teilaufgaben:
# 1. CSV laden, alle Textspalten bereinigen und fehlende/leer gewordene country-Werte auffüllen.
# 2. registered_at anhand der vorgegebenen eindeutigen Formate in YYYY-MM-DD überführen.
# 3. country über normalisierte deutsche/englische Namen sowie ISO-Kürzel auf ISO-Alpha-2 vereinheitlichen.
# 4. Das vollständige Ergebnis mit unveränderten übrigen Spalten als Parquet speichern.

input_path = Path(
    r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/customers_raw.csv"
)
output_path = Path(
    r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/cleaning/openai_v3_chain_of_thought/output.parquet"
)

# Schritt 1: Eingabedatei laden; pandas erhält die vorhandenen Spalten und ihre CSV-Inhalte.
df = pd.read_csv(input_path)

# Schritt 1: object- und String-Spalten sind Textspalten; str.strip() ist mit fehlenden Werten kompatibel.
text_columns = df.select_dtypes(include=["object", "string"]).columns.tolist()
for column in text_columns:
    df[column] = df[column].astype("string").str.strip()

# Schritt 1: Sowohl echte fehlende Werte als auch nach dem Trimmen leere Länderwerte werden UNKNOWN.
country_missing = df["country"].isna() | df["country"].eq("")
df.loc[country_missing, "country"] = "UNKNOWN"

# Schritt 2: Die Datumsformate werden explizit behandelt, damit keine versionsabhängige,
# mehrdeutige automatische Datumsinterpretation von pandas erforderlich ist.
def normalize_registered_at(value):
    if pd.isna(value):
        return pd.NA

    text = str(value).strip()
    if not text:
        return pd.NA

    # Unix-Timestamps in Sekunden; UTC verhindert eine lokale Zeitzonenverschiebung des Datums.
    if re.fullmatch(r"[+-]?\d{10}", text):
        try:
            return datetime.fromtimestamp(int(text), tz=timezone.utc).strftime("%Y-%m-%d")
        except (OverflowError, OSError, ValueError):
            return pd.NA

    # ISO-Datum und ISO-Datetime: zuerst die ersten zehn Zeichen als ISO-Datum validieren.
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:[T\s].*)?", text):
        try:
            return datetime.strptime(text[:10], "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            return pd.NA

    # Deutsches TT.MM.JJJJ.
    if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", text):
        try:
            return datetime.strptime(text, "%d.%m.%Y").strftime("%Y-%m-%d")
        except ValueError:
            return pd.NA

    # US-Format mit vollständigem oder abgekürztem englischem Monatsnamen.
    for date_format in ("%B %d %Y", "%B %d, %Y", "%b %d %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(text, date_format).strftime("%Y-%m-%d")
        except ValueError:
            pass

    # Nicht spezifizierte bzw. nicht valide Inhalte können nicht eindeutig normalisiert werden.
    return pd.NA


df["registered_at"] = df["registered_at"].map(normalize_registered_at).astype("string")

# Schritt 3: Länderwerte werden akzent-, groß/klein-, leerzeichen- und sonderzeichenunabhängig verglichen.
def country_key(value):
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.casefold().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", "", text)


# Jede Liste enthält ISO-Alpha-2, ggf. Alpha-3 sowie gebräuchliche englische und deutsche Varianten.
country_definitions = {
    "AF": ["AF", "AFG", "Afghanistan"],
    "AL": ["AL", "ALB", "Albania", "Albanien"],
    "DZ": ["DZ", "DZA", "Algeria", "Algerien"],
    "AD": ["AD", "AND", "Andorra"],
    "AO": ["AO", "AGO", "Angola"],
    "AR": ["AR", "ARG", "Argentina", "Argentinien"],
    "AM": ["AM", "ARM", "Armenia", "Armenien"],
    "AU": ["AU", "AUS", "Australia", "Australien"],
    "AT": ["AT", "AUT", "Austria", "Oesterreich", "Österreich"],
    "AZ": ["AZ", "AZE", "Azerbaijan", "Aserbaidschan"],
    "BS": ["BS", "BHS", "Bahamas", "The Bahamas"],
    "BH": ["BH", "BHR", "Bahrain", "Bahrain"],
    "BD": ["BD", "BGD", "Bangladesh", "Bangladesch"],
    "BB": ["BB", "BRB", "Barbados"],
    "BY": ["BY", "BLR", "Belarus", "Weissrussland", "Belarus"],
    "BE": ["BE", "BEL", "Belgium", "Belgien"],
    "BZ": ["BZ", "BLZ", "Belize"],
    "BJ": ["BJ", "BEN", "Benin"],
    "BT": ["BT", "BTN", "Bhutan", "Bhutan"],
    "BO": ["BO", "BOL", "Bolivia", "Bolivien"],
    "BA": ["BA", "BIH", "Bosnia and Herzegovina", "Bosnia Herzegovina", "Bosnien und Herzegowina", "Bosnien Herzegowina"],
    "BW": ["BW", "BWA", "Botswana"],
    "BR": ["BR", "BRA", "Brazil", "Brasilien"],
    "BN": ["BN", "BRN", "Brunei"],
    "BG": ["BG", "BGR", "Bulgaria", "Bulgarien"],
    "BF": ["BF", "BFA", "Burkina Faso"],
    "BI": ["BI", "BDI", "Burundi"],
    "KH": ["KH", "KHM", "Cambodia", "Kambodscha"],
    "CM": ["CM", "CMR", "Cameroon", "Kamerun"],
    "CA": ["CA", "CAN", "Canada", "Kanada"],
    "CV": ["CV", "CPV", "Cape Verde", "Cabo Verde", "Kap Verde"],
    "CF": ["CF", "CAF", "Central African Republic", "Central African Republic", "Zentralafrikanische Republik"],
    "TD": ["TD", "TCD", "Chad", "Tschad"],
    "CL": ["CL", "CHL", "Chile"],
    "CN": ["CN", "CHN", "China", "People's Republic of China", "Volksrepublik China"],
    "CO": ["CO", "COL", "Colombia", "Kolumbien"],
    "KM": ["KM", "COM", "Comoros", "Komoren"],
    "CD": ["CD", "COD", "Democratic Republic of the Congo", "DR Congo", "D R Congo", "Kongo Kinshasa", "Demokratische Republik Kongo"],
    "CG": ["CG", "COG", "Republic of the Congo", "Kongo Brazzaville", "Republik Kongo"],
    "CR": ["CR", "CRI", "Costa Rica"],
    "CI": ["CI", "CIV", "Cote d Ivoire", "Côte d'Ivoire", "Ivory Coast", "Elfenbeinkueste", "Elfenbeinküste"],
    "HR": ["HR", "HRV", "Croatia", "Kroatien"],
    "CU": ["CU", "CUB", "Cuba", "Kuba"],
    "CY": ["CY", "CYP", "Cyprus", "Zypern"],
    "CZ": ["CZ", "CZE", "Czechia", "Czech Republic", "Tschechien", "Tschechische Republik"],
    "DK": ["DK", "DNK", "Denmark", "Daenemark", "Dänemark"],
    "DJ": ["DJ", "DJI", "Djibouti", "Dschibuti"],
    "DM": ["DM", "DMA", "Dominica", "Dominica"],
    "DO": ["DO", "DOM", "Dominican Republic", "Dominikanische Republik"],
    "EC": ["EC", "ECU", "Ecuador"],
    "EG": ["EG", "EGY", "Egypt", "Aegypten", "Ägypten"],
    "SV": ["SV", "SLV", "El Salvador"],
    "GQ": ["GQ", "GNQ", "Equatorial Guinea", "Aequatorialguinea", "Äquatorialguinea"],
    "ER": ["ER", "ERI", "Eritrea"],
    "EE": ["EE", "EST", "Estonia", "Estland"],
    "SZ": ["SZ", "SWZ", "Eswatini", "Swaziland"],
    "ET": ["ET", "ETH", "Ethiopia", "Aethiopien", "Äthiopien"],
    "FJ": ["FJ", "FJI", "Fiji", "Fidschi"],
    "FI": ["FI", "FIN", "Finland", "Finnland"],
    "FR": ["FR", "FRA", "France", "Frankreich"],
    "GA": ["GA", "GAB", "Gabon"],
    "GM": ["GM", "GMB", "Gambia", "The Gambia"],
    "GE": ["GE", "GEO", "Georgia", "Georgien"],
    "DE": ["DE", "DEU", "GER", "Germany", "Deutschland", "Federal Republic of Germany", "Bundesrepublik Deutschland"],
    "GH": ["GH", "GHA", "Ghana"],
    "GR": ["GR", "GRC", "Greece", "Griechenland"],
    "GT": ["GT", "GTM", "Guatemala"],
    "GN": ["GN", "GIN", "Guinea", "Guinea"],
    "GW": ["GW", "GNB", "Guinea Bissau", "Guinea-Bissau"],
    "GY": ["GY", "GUY", "Guyana"],
    "HT": ["HT", "HTI", "Haiti", "Haiti"],
    "HN": ["HN", "HND", "Honduras"],
    "HU": ["HU", "HUN", "Hungary", "Ungarn"],
    "IS": ["IS", "ISL", "Iceland", "Island"],
    "IN": ["IN", "IND", "India", "Indien"],
    "ID": ["ID", "IDN", "Indonesia", "Indonesien"],
    "IR": ["IR", "IRN", "Iran", "Islamic Republic of Iran"],
    "IQ": ["IQ", "IRQ", "Iraq", "Irak"],
    "IE": ["IE", "IRL", "Ireland", "Irland"],
    "IL": ["IL", "ISR", "Israel"],
    "IT": ["IT", "ITA", "Italy", "Italien"],
    "JM": ["JM", "JAM", "Jamaica", "Jamaika"],
    "JP": ["JP", "JPN", "Japan", "Japan"],
    "JO": ["JO", "JOR", "Jordan", "Jordanien"],
    "KZ": ["KZ", "KAZ", "Kazakhstan", "Kasachstan"],
    "KE": ["KE", "KEN", "Kenya", "Kenia"],
    "KI": ["KI", "KIR", "Kiribati"],
    "KP": ["KP", "PRK", "North Korea", "Korea North", "Nordkorea"],
    "KR": ["KR", "KOR", "South Korea", "Korea South", "Suedkorea", "Südkorea", "Republic of Korea"],
    "KW": ["KW", "KWT", "Kuwait", "Kuwait"],
    "KG": ["KG", "KGZ", "Kyrgyzstan", "Kirgisistan"],
    "LA": ["LA", "LAO", "Laos"],
    "LV": ["LV", "LVA", "Latvia", "Lettland"],
    "LB": ["LB", "LBN", "Lebanon", "Libanon"],
    "LS": ["LS", "LSO", "Lesotho"],
    "LR": ["LR", "LBR", "Liberia"],
    "LY": ["LY", "LBY", "Libya", "Libyen"],
    "LI": ["LI", "LIE", "Liechtenstein"],
    "LT": ["LT", "LTU", "Lithuania", "Litauen"],
    "LU": ["LU", "LUX", "Luxembourg", "Luxemburg"],
    "MG": ["MG", "MDG", "Madagascar", "Madagaskar"],
    "MW": ["MW", "MWI", "Malawi"],
    "MY": ["MY", "MYS", "Malaysia", "Malaysia"],
    "MV": ["MV", "MDV", "Maldives", "Malediven"],
    "ML": ["ML", "MLI", "Mali"],
    "MT": ["MT", "MLT", "Malta"],
    "MH": ["MH", "MHL", "Marshall Islands", "Marshallinseln"],
    "MR": ["MR", "MRT", "Mauritania", "Mauretanien"],
    "MU": ["MU", "MUS", "Mauritius", "Mauritius"],
    "MX": ["MX", "MEX", "Mexico", "Mexiko"],
    "FM": ["FM", "FSM", "Micronesia", "Mikronesien"],
    "MD": ["MD", "MDA", "Moldova", "Moldawien"],
    "MC": ["MC", "MCO", "Monaco", "Monaco"],
    "MN": ["MN", "MNG", "Mongolia", "Mongolei"],
    "ME": ["ME", "MNE", "Montenegro"],
    "MA": ["MA", "MAR", "Morocco", "Marokko"],
    "MZ": ["MZ", "MOZ", "Mozambique", "Mosambik"],
    "MM": ["MM", "MMR", "Myanmar", "Burma", "Birma"],
    "NA": ["NA", "NAM", "Namibia"],
    "NR": ["NR", "NRU", "Nauru"],
    "NP": ["NP", "NPL", "Nepal"],
    "NL": ["NL", "NLD", "Netherlands", "Holland", "The Netherlands", "Niederlande"],
    "NZ": ["NZ", "NZL", "New Zealand", "Neuseeland"],
    "NI": ["NI", "NIC", "Nicaragua"],
    "NE": ["NE", "NER", "Niger"],
    "NG": ["NG", "NGA", "Nigeria", "Nigeria"],
    "MK": ["MK", "MKD", "North Macedonia", "Macedonia", "Nordmazedonien"],
    "NO": ["NO", "NOR", "Norway", "Norwegen"],
    "OM": ["OM", "OMN", "Oman"],
    "PK": ["PK", "PAK", "Pakistan"],
    "PW": ["PW", "PLW", "Palau"],
    "PA": ["PA", "PAN", "Panama", "Panama"],
    "PG": ["PG", "PNG", "Papua New Guinea", "Papua Neuguinea"],
    "PY": ["PY", "PRY", "Paraguay"],
    "PE": ["PE", "PER", "Peru"],
    "PH": ["PH", "PHL", "Philippines", "Philippinen"],
    "PL": ["PL", "POL", "Poland", "Polen"],
    "PT": ["PT", "PRT", "Portugal"],
    "QA": ["QA", "QAT", "Qatar", "Katar"],
    "RO": ["RO", "ROU", "ROM", "Romania", "Rumaenien", "Rumänien"],
    "RU": ["RU", "RUS", "Russian Federation", "Russia", "Russland"],
    "RW": ["RW", "RWA", "Rwanda", "Ruanda"],
    "KN": ["KN", "KNA", "Saint Kitts and Nevis", "St Kitts and Nevis"],
    "LC": ["LC", "LCA", "Saint Lucia", "St Lucia"],
    "VC": ["VC", "VCT", "Saint Vincent and the Grenadines", "St Vincent and the Grenadines"],
    "WS": ["WS", "WSM", "Samoa"],
    "SM": ["SM", "SMR", "San Marino"],
    "ST": ["ST", "STP", "Sao Tome and Principe", "Sao Tome und Principe"],
    "SA": ["SA", "SAU", "Saudi Arabia", "Saudi Arabien"],
    "SN": ["SN", "SEN", "Senegal"],
    "RS": ["RS", "SRB", "Serbia", "Serbien"],
    "SC": ["SC", "SYC", "Seychelles", "Seychellen"],
    "SL": ["SL", "SLE", "Sierra Leone"],
    "SG": ["SG", "SGP", "Singapore", "Singapur"],
    "SK": ["SK", "SVK", "Slovakia", "Slowakei"],
    "SI": ["SI", "SVN", "Slovenia", "Slowenien"],
    "SB": ["SB", "SLB", "Solomon Islands", "Salomonen"],
    "SO": ["SO", "SOM", "Somalia"],
    "ZA": ["ZA", "ZAF", "South Africa", "Suedafrika", "Südafrika"],
    "SS": ["SS", "SSD", "South Sudan", "Suedsudan", "Südsudan"],
    "ES": ["ES", "ESP", "Spain", "Spanien"],
    "LK": ["LK", "LKA", "Sri Lanka"],
    "SD": ["SD", "SDN", "Sudan"],
    "SR": ["SR", "SUR", "Suriname"],
    "SE": ["SE", "SWE", "Sweden", "Schweden"],
    "CH": ["CH", "CHE", "SUI", "Switzerland", "Schweiz"],
    "SY": ["SY", "SYR", "Syria", "Syrien"],
    "TW": ["TW", "TWN", "Taiwan"],
    "TJ": ["TJ", "TJK", "Tajikistan", "Tadschikistan"],
    "TZ": ["TZ", "TZA", "Tanzania", "Tansania"],
    "TH": ["TH", "THA", "Thailand", "Thailand"],
    "TL": ["TL", "TLS", "Timor Leste", "East Timor", "Osttimor"],
    "TG": ["TG", "TGO", "Togo"],
    "TO": ["TO", "TON", "Tonga"],
    "TT": ["TT", "TTO", "Trinidad and Tobago", "Trinidad und Tobago"],
    "TN": ["TN", "TUN", "Tunisia", "Tunesien"],
    "TR": ["TR", "TUR", "Turkey", "Turkiye", "Türkiye", "Tuerkei", "Türkei"],
    "TM": ["TM", "TKM", "Turkmenistan", "Turkmenistan"],
    "TV": ["TV", "TUV", "Tuvalu"],
    "UG": ["UG", "UGA", "Uganda"],
    "UA": ["UA", "UKR", "Ukraine", "Ukraine"],
    "AE": ["AE", "ARE", "United Arab Emirates", "UAE", "Vereinigte Arabische Emirate"],
    "GB": ["GB", "GBR", "UK", "U K", "United Kingdom", "Great Britain", "Britain", "England", "Vereinigtes Koenigreich", "Vereinigtes Königreich", "Grossbritannien", "Großbritannien"],
    "US": ["US", "USA", "United States", "United States of America", "America", "Vereinigte Staaten", "Vereinigte Staaten von Amerika"],
    "UY": ["UY", "URY", "Uruguay"],
    "UZ": ["UZ", "UZB", "Uzbekistan", "Usbekistan"],
    "VU": ["VU", "VUT", "Vanuatu"],
    "VA": ["VA", "VAT", "Vatican City", "Vatican", "Holy See", "Vatikanstadt", "Vatikan"],
    "VE": ["VE", "VEN", "Venezuela"],
    "VN": ["VN", "VNM", "Vietnam", "Viet Nam"],
    "YE": ["YE", "YEM", "Yemen", "Jemen"],
    "ZM": ["ZM", "ZMB", "Zambia", "Sambia"],
    "ZW": ["ZW", "ZWE", "Zimbabwe", "Simbabwe"],
}

country_lookup = {}
for iso2, aliases in country_definitions.items():
    for alias in aliases:
        country_lookup[country_key(alias)] = iso2

# UNKNOWN bleibt erhalten; alle nicht eindeutigen oder nicht bekannten Werte werden ebenfalls UNKNOWN.
def normalize_country(value):
    if pd.isna(value):
        return "UNKNOWN"
    return country_lookup.get(country_key(value), "UNKNOWN")


df["country"] = df["country"].map(normalize_country).astype("string")

# Schritt 4: Zielordner anlegen und ausschließlich das Ergebnis des letzten Transformationsschritts speichern.
output_path.parent.mkdir(parents=True, exist_ok=True)
df.to_parquet(output_path, index=False)