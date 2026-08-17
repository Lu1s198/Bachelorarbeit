# ETL-Aufgabe: Umsatzauswertung aus Kunden-, Produkt- und Bestelldaten
#
# Sub-Schritte:
# 1. Rohdaten einlesen
# 2. customers_raw: Leerzeichen in allen Textspalten trimmen
# 3. customers_raw: country -> country_code (ISO-3166-1 alpha-2) vereinheitlichen,
#    unbekannte/fehlende Werte -> 'UNKNOWN'
# 4. customers_raw: Duplikate nach customer_id entfernen (erstes Vorkommen behalten)
# 5. products_raw: price_eur -> float, in_stock -> bool konvertieren
# 6. orders_raw mit customers_raw (customer_id) und products_raw (product_id) mergen,
#    alle Bestellzeilen bleiben erhalten (left join)
# 7. Aggregation pro country_code & category: total_revenue_eur, order_count
# 8. Sortierung absteigend nach total_revenue_eur
# 9. Ergebnis als Parquet speichern

import pandas as pd
import numpy as np
import re

# --- Pfade ---
base_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_composite/2/codegen/anthropic_v3_chain_of_thought_r2/output.parquet"

# --- Schritt 1: Rohdaten einlesen ---
customers = pd.read_csv(f"{base_path}/customers_raw.csv", dtype=str)
products = pd.read_csv(f"{base_path}/products_raw.csv", dtype=str)
orders = pd.read_csv(f"{base_path}/orders_raw.csv", dtype=str)

# --- Schritt 2: Leerzeichen in allen Textspalten von customers_raw trimmen ---
for col in customers.columns:
    if customers[col].dtype == object:
        customers[col] = customers[col].str.strip()

# --- Schritt 3: country -> country_code vereinheitlichen ---
# Mapping-Tabelle fuer verschiedene Sprachen, Abkuerzungen und bekannte Tippfehler
country_mapping = {
    # Deutschland
    "de": "DE", "deu": "DE", "ger": "DE", "germany": "DE", "deutschland": "DE",
    "deutshcland": "DE", "deuschland": "DE", "germay": "DE", "allemagne": "DE",
    # Oesterreich
    "at": "AT", "aut": "AT", "austria": "AT", "oesterreich": "AT", "österreich": "AT",
    "osterreich": "AT", "austia": "AT",
    # Schweiz
    "ch": "CH", "che": "CH", "switzerland": "CH", "schweiz": "CH", "suisse": "CH",
    "svizzera": "CH", "swiss": "CH",
    # Frankreich
    "fr": "FR", "fra": "FR", "france": "FR", "frankreich": "FR", "franc": "FR",
    # Italien
    "it": "IT", "ita": "IT", "italy": "IT", "italien": "IT", "italia": "IT",
    # Spanien
    "es": "ES", "esp": "ES", "spain": "ES", "spanien": "ES", "espana": "ES", "españa": "ES",
    # Niederlande
    "nl": "NL", "nld": "NL", "netherlands": "NL", "niederlande": "NL", "holland": "NL",
    # Belgien
    "be": "BE", "bel": "BE", "belgium": "BE", "belgien": "BE", "belgique": "BE",
    # Grossbritannien
    "gb": "GB", "uk": "GB", "gbr": "GB", "united kingdom": "GB", "great britain": "GB",
    "grossbritannien": "GB", "großbritannien": "GB", "england": "GB",
    # USA
    "us": "US", "usa": "US", "united states": "US", "united states of america": "US",
    "vereinigte staaten": "US",
    # Polen
    "pl": "PL", "pol": "PL", "poland": "PL", "polen": "PL",
    # Portugal
    "pt": "PT", "prt": "PT", "portugal": "PT",
    # Tschechien
    "cz": "CZ", "cze": "CZ", "czech republic": "CZ", "tschechien": "CZ",
    # Daenemark
    "dk": "DK", "dnk": "DK", "denmark": "DK", "daenemark": "DK", "dänemark": "DK",
    # Schweden
    "se": "SE", "swe": "SE", "sweden": "SE", "schweden": "SE",
    # Norwegen
    "no": "NO", "nor": "NO", "norway": "NO", "norwegen": "NO",
    # Luxemburg
    "lu": "LU", "lux": "LU", "luxembourg": "LU", "luxemburg": "LU",
}

def normalize_country(value):
    """Ordnet einen Rohwert einem ISO-3166-1 alpha-2 Code zu."""
    if pd.isna(value) or str(value).strip() == "":
        return "UNKNOWN"
    key = str(value).strip().lower()
    # direkte Uebereinstimmung mit gemapptem Wert (z.B. schon 2-stelliger Code)
    if key in country_mapping:
        return country_mapping[key]
    # falls bereits ein gueltiger 2-stelliger Code direkt vorliegt (Grossbuchstaben)
    upper_val = str(value).strip().upper()
    if len(upper_val) == 2 and upper_val.isalpha() and upper_val in set(country_mapping.values()):
        return upper_val
    return "UNKNOWN"

customers["country_code"] = customers["country"].apply(normalize_country)

# --- Schritt 4: Duplikate nach customer_id entfernen (erstes Vorkommen behalten) ---
customers = customers.drop_duplicates(subset="customer_id", keep="first")

# --- Schritt 5: products_raw konvertieren ---
def parse_price(value):
    """Wandelt Preis-Strings wie '19,99' oder '19.99 EUR' in float um."""
    if pd.isna(value):
        return np.nan
    s = str(value)
    # entferne alles ausser Ziffern, Komma, Punkt und Minus
    s = re.sub(r"[^0-9,.\-]", "", s).strip()
    # falls sowohl Komma als auch Punkt vorkommen: Punkt = Tausendertrenner, Komma = Dezimal
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return np.nan

products["price_eur"] = products["price_eur"].apply(parse_price)

def parse_bool(value):
    """Wandelt verschiedene Boolean-Repraesentationen in echten bool um."""
    if pd.isna(value):
        return np.nan
    s = str(value).strip().lower()
    true_vals = {"true", "1", "yes", "ja", "y", "wahr", "t"}
    false_vals = {"false", "0", "no", "nein", "n", "falsch", "f"}
    if s in true_vals:
        return True
    if s in false_vals:
        return False
    return np.nan

products["in_stock"] = products["in_stock"].apply(parse_bool)

# --- Schritt 6: orders_raw mit customers und products mergen (left join, alle Bestellzeilen bleiben) ---
# numerische Spalten in orders_raw konvertieren
orders["quantity"] = pd.to_numeric(orders["quantity"], errors="coerce")
orders["unit_price_eur"] = orders["unit_price_eur"].apply(parse_price)

merged = orders.merge(customers, on="customer_id", how="left", suffixes=("", "_cust"))
merged = merged.merge(products, on="product_id", how="left", suffixes=("", "_prod"))

# fehlende country_code (z.B. wenn customer_id nicht gefunden wurde) -> UNKNOWN
merged["country_code"] = merged["country_code"].fillna("UNKNOWN")

# --- Schritt 7: Aggregation pro country_code & category ---
merged["line_revenue"] = merged["quantity"] * merged["unit_price_eur"]

agg = (
    merged.groupby(["country_code", "category"], dropna=False)
    .agg(
        total_revenue_eur=("line_revenue", "sum"),
        order_count=("line_revenue", "count"),
    )
    .reset_index()
)

agg["total_revenue_eur"] = agg["total_revenue_eur"].round(2)

# --- Schritt 8: Sortierung absteigend nach total_revenue_eur ---
agg = agg.sort_values(by="total_revenue_eur", ascending=False).reset_index(drop=True)

# --- Schritt 9: Ergebnis als Parquet speichern ---
agg.to_parquet(output_path, index=False)