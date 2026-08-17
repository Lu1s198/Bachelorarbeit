import pandas as pd
import numpy as np
import re

# -----------------------------------------------------------------
# Pfade definieren
# -----------------------------------------------------------------
base_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_composite/2/codegen/anthropic_v3_chain_of_thought/output.parquet"

customers_path = f"{base_path}/customers_raw.csv"
products_path = f"{base_path}/products_raw.csv"
orders_path = f"{base_path}/orders_raw.csv"

# -----------------------------------------------------------------
# Sub-Schritte (siehe Aufgabenstellung):
# 1. Textspalten in customers_raw trimmen
# 2. country -> country_code (ISO-3166-1-alpha-2) normalisieren
# 3. Duplikate in customer_id entfernen (erstes Vorkommen behalten)
# 4. products_raw: price_eur -> float, in_stock -> bool
# 5. orders_raw mit customers_raw und products_raw joinen (left join, orders bleiben vollstaendig)
# 6. Aggregation pro country_code und category: total_revenue_eur, order_count, sortiert absteigend
# -----------------------------------------------------------------

# -----------------------------------------------------------------
# Schritt 0: Rohdaten einlesen
# -----------------------------------------------------------------
customers = pd.read_csv(customers_path, dtype=str)
products = pd.read_csv(products_path, dtype=str)
orders = pd.read_csv(orders_path, dtype=str)

# -----------------------------------------------------------------
# Schritt 1: Leerzeichen aus allen Textspalten von customers entfernen
# -----------------------------------------------------------------
for col in customers.columns:
    if customers[col].dtype == object:
        customers[col] = customers[col].str.strip()

# -----------------------------------------------------------------
# Schritt 2: country -> country_code normalisieren
# -----------------------------------------------------------------
# Mapping-Tabelle fuer bekannte Varianten (verschiedene Sprachen, Abkuerzungen, Tippfehler)
country_mapping = {
    # Deutschland
    "deutschland": "DE", "germany": "DE", "ger": "DE", "de": "DE",
    "deutshcland": "DE", "allemagne": "DE", "deuschland": "DE",
    "deutschlnad": "DE",

    # Frankreich
    "frankreich": "FR", "france": "FR", "fra": "FR", "fr": "FR",
    "franc": "FR", "francia": "FR",

    # Oesterreich
    "österreich": "AT", "oesterreich": "AT", "austria": "AT",
    "aut": "AT", "at": "AT",

    # Schweiz
    "schweiz": "CH", "switzerland": "CH", "suisse": "CH",
    "svizzera": "CH", "ch": "CH", "sui": "CH",

    # Italien
    "italien": "IT", "italy": "IT", "italia": "IT", "ita": "IT", "it": "IT",

    # Spanien
    "spanien": "ES", "spain": "ES", "espana": "ES", "españa": "ES",
    "esp": "ES", "es": "ES",

    # Niederlande
    "niederlande": "NL", "netherlands": "NL", "holland": "NL",
    "nl": "NL", "ned": "NL",

    # Belgien
    "belgien": "BE", "belgium": "BE", "belgique": "BE", "be": "BE",

    # Polen
    "polen": "PL", "poland": "PL", "pl": "PL",

    # Vereinigtes Koenigreich
    "vereinigtes königreich": "GB", "united kingdom": "GB", "uk": "GB",
    "great britain": "GB", "gb": "GB", "england": "GB",

    # USA
    "usa": "US", "united states": "US", "united states of america": "US",
    "us": "US", "vereinigte staaten": "US",

    # Portugal
    "portugal": "PT", "por": "PT", "pt": "PT",

    # Schweden
    "schweden": "SE", "sweden": "SE", "se": "SE",

    # Daenemark
    "dänemark": "DK", "daenemark": "DK", "denmark": "DK", "dk": "DK",
}

def normalize_country(value):
    """Wandelt einen Rohwert der country-Spalte in einen ISO-3166-1-alpha-2 Code um."""
    if pd.isna(value) or str(value).strip() == "":
        return "UNKNOWN"
    key = str(value).strip().lower()
    # direkte Zuordnung ueber Mapping-Tabelle
    if key in country_mapping:
        return country_mapping[key]
    # falls bereits ein gueltiger 2-stelliger Code (Grossbuchstaben) vorliegt
    key_upper = str(value).strip().upper()
    if len(key_upper) == 2 and key_upper.isalpha():
        # Nur akzeptieren, wenn es sich um einen der bekannten Codes handelt
        known_codes = set(country_mapping.values())
        if key_upper in known_codes:
            return key_upper
    return "UNKNOWN"

customers["country_code"] = customers["country"].apply(normalize_country)

# -----------------------------------------------------------------
# Schritt 3: Duplikate in customer_id entfernen (erstes Vorkommen behalten)
# -----------------------------------------------------------------
customers = customers.drop_duplicates(subset="customer_id", keep="first")

# -----------------------------------------------------------------
# Schritt 4: products_raw aufbereiten
# -----------------------------------------------------------------
def parse_price(value):
    """Wandelt Preistext (z.B. '19,99', '19.99 EUR') in float um."""
    if pd.isna(value):
        return np.nan
    s = str(value)
    # Waehrungsbezeichner und Leerzeichen entfernen
    s = re.sub(r"[^\d,.\-]", "", s)
    # Falls Komma als Dezimaltrennzeichen verwendet wird (deutsches Format)
    if "," in s and "." in s:
        # Tausendertrennzeichen entfernen, Komma als Dezimaltrennzeichen
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return np.nan

products["price_eur"] = products["price_eur"].apply(parse_price)

def parse_bool(value):
    """Wandelt verschiedene Darstellungen von in_stock in einen Boolean um."""
    if pd.isna(value):
        return False
    s = str(value).strip().lower()
    true_values = {"true", "1", "yes", "ja", "y", "wahr"}
    false_values = {"false", "0", "no", "nein", "n", "falsch"}
    if s in true_values:
        return True
    elif s in false_values:
        return False
    else:
        return False  # unklare Werte konservativ als False behandeln

products["in_stock"] = products["in_stock"].apply(parse_bool)

# -----------------------------------------------------------------
# Schritt 5: orders_raw mit customers und products joinen (left join)
# -----------------------------------------------------------------
# Numerische Spalten in orders_raw korrekt typisieren
orders["quantity"] = pd.to_numeric(orders["quantity"], errors="coerce")
orders["unit_price_eur"] = orders["unit_price_eur"].apply(parse_price)

merged = orders.merge(customers, on="customer_id", how="left", suffixes=("", "_cust"))
merged = merged.merge(products, on="product_id", how="left", suffixes=("", "_prod"))

# -----------------------------------------------------------------
# Schritt 6: Aggregation pro country_code und category
# -----------------------------------------------------------------
merged["revenue"] = merged["quantity"] * merged["unit_price_eur"]

# Fehlende country_code (z.B. wenn kein Match gefunden wurde) als 'UNKNOWN' behandeln
merged["country_code"] = merged["country_code"].fillna("UNKNOWN")

result = (
    merged.groupby(["country_code", "category"], dropna=False)
    .agg(
        total_revenue_eur=("revenue", "sum"),
        order_count=("revenue", "count"),
    )
    .reset_index()
)

result["total_revenue_eur"] = result["total_revenue_eur"].round(2)

result = result.sort_values("total_revenue_eur", ascending=False).reset_index(drop=True)

# -----------------------------------------------------------------
# Ergebnis als Parquet speichern
# -----------------------------------------------------------------
result.to_parquet(output_path, index=False)