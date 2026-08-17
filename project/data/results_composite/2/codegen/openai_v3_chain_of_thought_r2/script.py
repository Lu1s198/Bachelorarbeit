import os
import re
import unicodedata
from difflib import get_close_matches

import pandas as pd

# Teilaufgaben:
# 1. Rohdateien einlesen und Textspalten der Kundendaten bereinigen.
# 2. Länderwerte anhand einer kontrollierten Alias-Tabelle in ISO-Alpha-2-Codes überführen.
# 3. Doppelte customer_id-Werte entfernen und das erste Vorkommen behalten.
# 4. Preis- und Lagerbestandswerte der Produktdaten in passende Datentypen konvertieren.
# 5. Bestellungen per Left Join mit Kunden und Produkten anreichern, damit jede Bestellzeile erhalten bleibt.
# 6. Umsatz und Bestellanzahl nach Land und Kategorie aggregieren, sortieren und als Parquet speichern.

input_dir = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2"
output_path = (
    r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/"
    r"results_composite/2/codegen/openai_v3_chain_of_thought_r2/output.parquet"
)

customers = pd.read_csv(os.path.join(input_dir, "customers_raw.csv"))
products = pd.read_csv(os.path.join(input_dir, "products_raw.csv"))
orders = pd.read_csv(os.path.join(input_dir, "orders_raw.csv"))

# Schritt 1: Führende und nachfolgende Leerzeichen aus sämtlichen Textspalten entfernen.
customer_text_columns = customers.select_dtypes(include=["object", "string"]).columns
for column in customer_text_columns:
    customers[column] = customers[column].astype("string").str.strip()

# Hilfsfunktion: Länderbezeichnungen vergleichbar machen, ohne die Originalwerte zu verändern.
def normalize_country_value(value):
    if pd.isna(value):
        return None
    value = str(value).strip()
    if not value:
        return None
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "", value)
    return value or None

# Schritt 2: Kontrollierte Zuordnung häufiger deutscher, englischer und abgekürzter Länderwerte.
country_aliases = {
    "DE": ["de", "deu", "ger", "deutschland", "deutshcland", "germany", "allemagne"],
    "AT": ["at", "aut", "austria", "osterreich", "österreich", "australie"],
    "CH": ["ch", "che", "switzerland", "schweiz", "suisse", "svizzera"],
    "GB": [
        "gb", "uk", "gbr", "unitedkingdom", "greatbritain", "britain",
        "england", "vereinigteskonigreich", "vereinigteskönigreich",
    ],
    "US": [
        "us", "usa", "unitedstates", "unitedstatesofamerica", "america",
        "vereinigtestaaten", "vereinigtestaatenvonamerika",
    ],
    "FR": ["fr", "fra", "france", "frankreich"],
    "ES": ["es", "esp", "spain", "spanien", "espana", "españa"],
    "IT": ["it", "ita", "italy", "italien"],
    "NL": ["nl", "nld", "netherlands", "holland", "niederlande"],
    "BE": ["be", "bel", "belgium", "belgien", "belgique"],
    "LU": ["lu", "lux", "luxembourg", "luxemburg"],
    "PL": ["pl", "pol", "poland", "polen"],
    "CZ": ["cz", "cze", "czechia", "czechrepublic", "tschechien"],
    "SK": ["sk", "svk", "slovakia", "slowakei"],
    "HU": ["hu", "hun", "hungary", "ungarn"],
    "DK": ["dk", "dnk", "denmark", "danemark", "dänemark"],
    "SE": ["se", "swe", "sweden", "schweden"],
    "NO": ["no", "nor", "norway", "norwegen"],
    "FI": ["fi", "fin", "finland", "finnland"],
    "IE": ["ie", "irl", "ireland", "irland"],
    "PT": ["pt", "prt", "portugal"],
    "GR": ["gr", "grc", "greece", "griechenland", "hellas"],
    "RO": ["ro", "rou", "romania", "rumania", "rumanien"],
    "BG": ["bg", "bgr", "bulgaria", "bulgarien"],
    "HR": ["hr", "hrv", "croatia", "kroatien"],
    "SI": ["si", "svn", "slovenia", "slowenien"],
    "RS": ["rs", "srb", "serbia", "serbien"],
    "TR": ["tr", "tur", "turkey", "türkiye", "turkei", "türkei"],
    "CA": ["ca", "can", "canada"],
    "MX": ["mx", "mex", "mexico", "mexiko"],
    "BR": ["br", "bra", "brazil", "brasilien"],
    "AR": ["ar", "arg", "argentina", "argentinien"],
    "AU": ["au", "aus", "australia", "australien"],
    "NZ": ["nz", "nzl", "newzealand", "neuseeland"],
    "JP": ["jp", "jpn", "japan"],
    "CN": ["cn", "chn", "china", "volksrepublikchina"],
    "IN": ["in", "ind", "india", "indien"],
    "KR": ["kr", "kor", "southkorea", "korea", "sudkorea"],
    "SG": ["sg", "sgp", "singapore", "singapur"],
    "ZA": ["za", "zaf", "southafrica", "sudafrika"],
    "AE": ["ae", "are", "unitedarabemirates", "vae", "vereinigtearabischeemirate"],
}

alias_to_code = {}
for code, aliases in country_aliases.items():
    for alias in aliases:
        normalized_alias = normalize_country_value(alias)
        if normalized_alias is not None:
            alias_to_code[normalized_alias] = code

def to_country_code(value):
    normalized_value = normalize_country_value(value)
    if normalized_value is None:
        return "UNKNOWN"

    if normalized_value in alias_to_code:
        return alias_to_code[normalized_value]

    # Tippfehler werden nur übernommen, wenn genau ein sehr ähnlicher bekannter Alias existiert.
    matches = get_close_matches(normalized_value, list(alias_to_code), n=2, cutoff=0.88)
    if len(matches) == 1:
        return alias_to_code[matches[0]]

    return "UNKNOWN"

if "country" in customers.columns:
    customers["country_code"] = customers["country"].map(to_country_code)
else:
    customers["country_code"] = "UNKNOWN"

# Schritt 3: Kunden-Dubletten anhand der customer_id auf das erste Vorkommen reduzieren.
customers = customers.drop_duplicates(subset=["customer_id"], keep="first")

# Hilfsfunktion für Preise mit Dezimalpunkt, Dezimalkomma und optionalem Währungssuffix.
def parse_decimal(value):
    if pd.isna(value):
        return pd.NA

    text = str(value).strip()
    if not text:
        return pd.NA

    text = re.sub(r"[^0-9,.\-+]", "", text)
    if not text or text in {"-", "+", ".", ","}:
        return pd.NA

    if "," in text and "." in text:
        # Das zuletzt auftretende Trennzeichen wird als Dezimaltrennzeichen interpretiert.
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")

    return pd.to_numeric(text, errors="coerce")

# Schritt 4: price_eur in Float und in_stock in einen nullable Boolean konvertieren.
products["price_eur"] = products["price_eur"].map(parse_decimal).astype(float)

boolean_values = {
    "true": True,
    "1": True,
    "yes": True,
    "y": True,
    "ja": True,
    "j": True,
    "in stock": True,
    "instock": True,
    "available": True,
    "verfuegbar": True,
    "verfügbar": True,
    "false": False,
    "0": False,
    "no": False,
    "n": False,
    "nein": False,
    "out of stock": False,
    "outofstock": False,
    "unavailable": False,
    "nicht verfuegbar": False,
    "nicht verfügbar": False,
}

products["in_stock"] = (
    products["in_stock"]
    .astype("string")
    .str.strip()
    .str.lower()
    .map(boolean_values)
    .astype("boolean")
)

# Schritt 5: Left Joins stellen sicher, dass keine Bestellzeile verloren geht.
orders_enriched = orders.merge(
    customers[["customer_id", "country_code"]],
    on="customer_id",
    how="left",
)

orders_enriched = orders_enriched.merge(
    products[["product_id", "category", "price_eur", "in_stock"]],
    on="product_id",
    how="left",
)

orders_enriched["country_code"] = orders_enriched["country_code"].fillna("UNKNOWN")
orders_enriched["category"] = orders_enriched["category"].fillna("UNKNOWN")

# Für die Berechnung werden ausschließlich quantity und unit_price_eur aus orders_raw.csv verwendet.
orders_enriched["quantity_numeric"] = orders_enriched["quantity"].map(parse_decimal)
orders_enriched["unit_price_numeric"] = orders_enriched["unit_price_eur"].map(parse_decimal)
orders_enriched["revenue_eur"] = (
    orders_enriched["quantity_numeric"] * orders_enriched["unit_price_numeric"]
)

# Schritt 6: Umsatz und Anzahl eindeutiger Bestellungen pro Land und Produktkategorie aggregieren.
group_columns = ["country_code", "category"]

if "order_id" in orders_enriched.columns:
    result = (
        orders_enriched.groupby(group_columns, dropna=False)
        .agg(
            total_revenue_eur=("revenue_eur", lambda values: values.sum(min_count=1)),
            order_count=("order_id", "nunique"),
        )
        .reset_index()
    )
else:
    result = (
        orders_enriched.groupby(group_columns, dropna=False)
        .agg(
            total_revenue_eur=("revenue_eur", lambda values: values.sum(min_count=1)),
            order_count=("revenue_eur", "size"),
        )
        .reset_index()
    )

result["total_revenue_eur"] = result["total_revenue_eur"].round(2)
result = result.sort_values(
    by="total_revenue_eur",
    ascending=False,
    na_position="last",
    kind="stable",
).reset_index(drop=True)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)