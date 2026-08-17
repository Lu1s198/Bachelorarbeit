import os
import re
import pandas as pd

# Schritt 1: Eingabedatei laden und alle Textspalten von führenden/nachfolgenden
# Leerzeichen bereinigen, ohne nicht-textuelle Spalten zu verändern.
input_path = (
    r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/"
    r"customers_raw.csv"
)
output_path = (
    r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/"
    r"cleaning/openai_v3_chain_of_thought_r2/output.parquet"
)

df = pd.read_csv(input_path)

# Sowohl object- als auch pandas-String-Spalten werden berücksichtigt, damit das
# Skript mit unterschiedlichen pandas-Versionen und CSV-Inferenz-Ergebnissen läuft.
text_columns = df.select_dtypes(include=["object", "string"]).columns
for column in text_columns:
    df[column] = df[column].map(
        lambda value: value.strip() if isinstance(value, str) else value
    )

# Fehlende country-Werte werden gemäß Vorgabe ersetzt. Leere, nach dem Trimmen
# entstandene Texte werden ebenfalls als nicht verwertbare Länderwerte behandelt.
df["country"] = df["country"].fillna("UNKNOWN")
df.loc[df["country"].astype(str).str.strip().eq(""), "country"] = "UNKNOWN"

# Schritt 2: registered_at aus ISO-, deutschem, englischem Monats- und Unix-Format
# einheitlich als ISO-Datum YYYY-MM-DD erzeugen.
def normalize_registered_at(value):
    # Fehlende oder leere Datumswerte bleiben fehlend.
    if pd.isna(value):
        return pd.NA

    text = str(value).strip()
    if not text:
        return pd.NA

    # Unix-Timestamps sind typischerweise 9 bis 11 Ziffern lang und werden als
    # Sekunden seit 1970 interpretiert. Kürzere Zahlen werden nicht irrtümlich
    # als Unix-Timestamps behandelt.
    if re.fullmatch(r"[+-]?\d{9,11}(?:\.0+)?", text):
        try:
            timestamp = pd.to_datetime(float(text), unit="s", errors="coerce")
            return timestamp.strftime("%Y-%m-%d") if not pd.isna(timestamp) else pd.NA
        except (ValueError, OverflowError):
            return pd.NA

    # ISO-Datumswerte werden zuerst streng verarbeitet.
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        parsed = pd.to_datetime(text, format="%Y-%m-%d", errors="coerce")
        return parsed.strftime("%Y-%m-%d") if not pd.isna(parsed) else pd.NA

    # Deutsche Formate TT.MM.JJJJ werden strikt vor anderen Textformaten geprüft.
    if re.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{4}", text):
        parsed = pd.to_datetime(text, format="%d.%m.%Y", errors="coerce")
        return parsed.strftime("%Y-%m-%d") if not pd.isna(parsed) else pd.NA

    # Englische Monatsnamen wie "January 31 2024" werden durch pandas geparst.
    parsed = pd.to_datetime(text, errors="coerce")
    return parsed.strftime("%Y-%m-%d") if not pd.isna(parsed) else pd.NA


df["registered_at"] = df["registered_at"].map(normalize_registered_at)

# Schritt 3: country auf ISO-3166-1-alpha-2 normalisieren. Eindeutige deutsche
# und englische Varianten werden zuerst über explizite Alias-Werte abgedeckt.
country_aliases = {
    "UNKNOWN": "UNKNOWN",
    "UNBEKANNT": "UNKNOWN",
    "N/A": "UNKNOWN",
    "NA": "UNKNOWN",
    "NONE": "UNKNOWN",
    "NULL": "UNKNOWN",
    "DE": "DE",
    "DEU": "DE",
    "GER": "DE",
    "DEUTSCHLAND": "DE",
    "GERMANY": "DE",
    "BUNDESREPUBLIK DEUTSCHLAND": "DE",
    "AT": "AT",
    "AUT": "AT",
    "ÖSTERREICH": "AT",
    "OESTERREICH": "AT",
    "AUSTRIA": "AT",
    "CH": "CH",
    "CHE": "CH",
    "SCHWEIZ": "CH",
    "SWITZERLAND": "CH",
    "LI": "LI",
    "LIE": "LI",
    "LIECHTENSTEIN": "LI",
    "GB": "GB",
    "UK": "GB",
    "UKM": "GB",
    "GBR": "GB",
    "UNITED KINGDOM": "GB",
    "GREAT BRITAIN": "GB",
    "BRITAIN": "GB",
    "ENGLAND": "GB",
    "SCOTLAND": "GB",
    "WALES": "GB",
    "NORDIRLAND": "GB",
    "NORTHERN IRELAND": "GB",
    "US": "US",
    "USA": "US",
    "UNITED STATES": "US",
    "UNITED STATES OF AMERICA": "US",
    "VEREINIGTE STAATEN": "US",
    "VEREINIGTE STAATEN VON AMERIKA": "US",
    "AMERICA": "US",
    "CA": "CA",
    "CAN": "CA",
    "CANADA": "CA",
    "FR": "FR",
    "FRA": "FR",
    "FRANCE": "FR",
    "FRANKREICH": "FR",
    "ES": "ES",
    "ESP": "ES",
    "SPAIN": "ES",
    "SPANIEN": "ES",
    "IT": "IT",
    "ITA": "IT",
    "ITALY": "IT",
    "ITALIEN": "IT",
    "NL": "NL",
    "NLD": "NL",
    "NETHERLANDS": "NL",
    "THE NETHERLANDS": "NL",
    "HOLLAND": "NL",
    "NIEDERLANDE": "NL",
    "BE": "BE",
    "BEL": "BE",
    "BELGIUM": "BE",
    "BELGIEN": "BE",
    "LU": "LU",
    "LUX": "LU",
    "LUXEMBOURG": "LU",
    "DK": "DK",
    "DNK": "DK",
    "DENMARK": "DK",
    "DÄNEMARK": "DK",
    "DAENEMARK": "DK",
    "SE": "SE",
    "SWE": "SE",
    "SWEDEN": "SE",
    "SCHWEDEN": "SE",
    "NO": "NO",
    "NOR": "NO",
    "NORWAY": "NO",
    "NORWEGEN": "NO",
    "FI": "FI",
    "FIN": "FI",
    "FINLAND": "FI",
    "FINNLAND": "FI",
    "PL": "PL",
    "POL": "PL",
    "POLAND": "PL",
    "POLEN": "PL",
    "CZ": "CZ",
    "CZE": "CZ",
    "CZECHIA": "CZ",
    "CZECH REPUBLIC": "CZ",
    "TSCHECHIEN": "CZ",
    "SK": "SK",
    "SVK": "SK",
    "SLOVAKIA": "SK",
    "SLOWAKEI": "SK",
    "HU": "HU",
    "HUN": "HU",
    "HUNGARY": "HU",
    "UNGARN": "HU",
    "RO": "RO",
    "ROU": "RO",
    "ROMANIA": "RO",
    "RUMÄNIEN": "RO",
    "BG": "BG",
    "BGR": "BG",
    "BULGARIA": "BG",
    "BULGARIEN": "BG",
    "HR": "HR",
    "HRV": "HR",
    "CROATIA": "HR",
    "KROATIEN": "HR",
    "SI": "SI",
    "SVN": "SI",
    "SLOVENIA": "SI",
    "SLOWENIEN": "SI",
    "GR": "GR",
    "GRC": "GR",
    "GREECE": "GR",
    "GRIECHENLAND": "GR",
    "PT": "PT",
    "PRT": "PT",
    "PORTUGAL": "PT",
    "IE": "IE",
    "IRL": "IE",
    "IRELAND": "IE",
    "IRLAND": "IE",
    "AU": "AU",
    "AUS": "AU",
    "AUSTRALIA": "AU",
    "NZ": "NZ",
    "NZL": "NZ",
    "NEW ZEALAND": "NZ",
    "NEUSEELAND": "NZ",
    "JP": "JP",
    "JPN": "JP",
    "JAPAN": "JP",
    "CN": "CN",
    "CHN": "CN",
    "CHINA": "CN",
    "IN": "IN",
    "IND": "IN",
    "INDIA": "IN",
    "INDIEN": "IN",
    "BR": "BR",
    "BRA": "BR",
    "BRAZIL": "BR",
    "BRASILIEN": "BR",
    "MX": "MX",
    "MEX": "MX",
    "MEXICO": "MX",
    "MEXIKO": "MX",
    "AR": "AR",
    "ARG": "AR",
    "ARGENTINA": "AR",
    "ZA": "ZA",
    "ZAF": "ZA",
    "SOUTH AFRICA": "ZA",
    "SÜDAFRIKA": "ZA",
    "SUEDAFRIKA": "ZA",
    "TR": "TR",
    "TUR": "TR",
    "TÜRKIYE": "TR",
    "TURKIYE": "TR",
    "TURKEY": "TR",
    "TÜRKEI": "TR",
    "TURKEI": "TR",
    "IL": "IL",
    "ISR": "IL",
    "ISRAEL": "IL",
    "AE": "AE",
    "ARE": "AE",
    "UAE": "AE",
    "UNITED ARAB EMIRATES": "AE",
    "VEREINIGTE ARABISCHE EMIRATE": "AE",
    "RU": "RU",
    "RUS": "RU",
    "RUSSIA": "RU",
    "RUSSIAN FEDERATION": "RU",
    "RUSSLAND": "RU",
    # Diese Begriffe sind ohne weitere Information nicht eindeutig.
    "CONGO": "UNKNOWN",
    "KOREA": "UNKNOWN",
}

# pycountry ergänzt die Alias-Liste um offizielle englische ISO-Namen sowie Alpha-3-Codes.
try:
    import pycountry

    for country in pycountry.countries:
        country_aliases.setdefault(country.alpha_2.upper(), country.alpha_2)
        country_aliases.setdefault(country.alpha_3.upper(), country.alpha_2)
        country_aliases.setdefault(country.name.upper(), country.alpha_2)
        if hasattr(country, "official_name"):
            country_aliases.setdefault(country.official_name.upper(), country.alpha_2)
        if hasattr(country, "common_name"):
            country_aliases.setdefault(country.common_name.upper(), country.alpha_2)
except ImportError:
    # Die explizite Alias-Tabelle ermöglicht auch ohne optionale Zusatzbibliothek
    # eine stabile Normalisierung der üblichen deutsch- und englischsprachigen Werte.
    pass


def normalize_country(value):
    if pd.isna(value):
        return "UNKNOWN"

    normalized = str(value).strip().upper()
    normalized = re.sub(r"\s+", " ", normalized)

    if not normalized or normalized in {"NAN", "<NA>"}:
        return "UNKNOWN"

    return country_aliases.get(normalized, "UNKNOWN")


df["country"] = df["country"].map(normalize_country)

# Nur das Endergebnis von Schritt 3 wird als Parquet-Datei am exakt vorgegebenen
# Zielpfad geschrieben; alle ursprünglich eingelesenen Spalten bleiben erhalten.
os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)