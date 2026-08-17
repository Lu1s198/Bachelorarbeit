import os
import re
import unicodedata
from difflib import SequenceMatcher

import pandas as pd

# Schritt 1: Eingabe- und Ausgabepfade definieren und die drei Rohtabellen laden.
base_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2"
output_path = (
    r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/"
    r"results_composite/2/codegen/openai_v3_chain_of_thought/output.parquet"
)

customers = pd.read_csv(os.path.join(base_path, "customers_raw.csv"))
products = pd.read_csv(os.path.join(base_path, "products_raw.csv"))
orders = pd.read_csv(os.path.join(base_path, "orders_raw.csv"))

# Schritt 2: Führende und nachfolgende Leerzeichen aus allen Textspalten
# der Kundendaten entfernen, ohne fehlende Werte in Strings umzuwandeln.
text_columns = customers.select_dtypes(include=["object", "string"]).columns
for column in text_columns:
    customers[column] = customers[column].map(
        lambda value: value.strip() if isinstance(value, str) else value
    )

# Schritt 3: Länderbezeichnungen vereinheitlichen.
# Zuerst werden Texte normalisiert, damit Groß-/Kleinschreibung, Akzente,
# Leerzeichen, Punkte und Sonderzeichen die Zuordnung nicht beeinflussen.
def normalize_country_value(value):
    if pd.isna(value):
        return None

    value = str(value).strip()
    if not value:
        return None

    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.casefold()
    value = re.sub(r"[^a-z0-9]+", "", value)
    return value or None


# Die Zuordnung enthält deutsche, englische und häufig verwendete
# internationale Schreibweisen, Abkürzungen sowie bekannte Tippfehler.
country_aliases = {
    "DE": {
        "de", "deu", "ger", "deutschland", "germany", "federalrepublicofgermany",
        "bundesrepublikdeutschland", "deutshcland", "deutchland", "deutschlnd",
        "germnay", "germani",
    },
    "AT": {
        "at", "aut", "osterreich", "austria", "oesterreich", "osterreichrepublik",
    },
    "CH": {
        "ch", "che", "schweiz", "switzerland", "suisse", "svizzera", "svizra",
    },
    "FR": {
        "fr", "fra", "fre", "france", "frankreich", "republiquefrancaise",
    },
    "IT": {
        "it", "ita", "italy", "italien", "italia",
    },
    "ES": {
        "es", "esp", "spain", "spanien", "espana",
    },
    "PT": {
        "pt", "prt", "portugal",
    },
    "NL": {
        "nl", "nld", "netherlands", "holland", "niederlande", "nederland",
    },
    "BE": {
        "be", "bel", "belgium", "belgien", "belgique", "belgie",
    },
    "LU": {
        "lu", "lux", "luxembourg", "luxemburg",
    },
    "GB": {
        "gb", "uk", "gbr", "unitedkingdom", "greatbritain", "britannien",
        "grossbritannien", "england", "vereinigteskonigreich",
    },
    "IE": {
        "ie", "irl", "ireland", "irland",
    },
    "US": {
        "us", "usa", "unitedstates", "unitedstatesofamerica", "america",
        "vereinigtestaaten", "vereinigtestaatenvonamerika",
    },
    "CA": {
        "ca", "can", "canada", "kanada",
    },
    "MX": {
        "mx", "mex", "mexico", "mexiko",
    },
    "BR": {
        "br", "bra", "brazil", "brasil", "brasilien",
    },
    "AR": {
        "ar", "arg", "argentina", "argentinien",
    },
    "CL": {
        "cl", "chl", "chile",
    },
    "CO": {
        "co", "col", "colombia", "kolumbien",
    },
    "PL": {
        "pl", "pol", "poland", "polen", "polska",
    },
    "CZ": {
        "cz", "cze", "czechia", "czechrepublic", "tschechien",
    },
    "DK": {
        "dk", "dnk", "denmark", "danemark", "dannemark",
    },
    "SE": {
        "se", "swe", "sweden", "schweden", "sverige",
    },
    "NO": {
        "no", "nor", "norway", "norwegen", "norge",
    },
    "FI": {
        "fi", "fin", "finland", "finnland", "suomi",
    },
    "RO": {
        "ro", "rou", "romania", "rumanien", "romania",
    },
    "HU": {
        "hu", "hun", "hungary", "ungarn", "magyarorszag",
    },
    "GR": {
        "gr", "greece", "griechenland", "hellas", "ellada",
    },
    "TR": {
        "tr", "tur", "turkey", "turkiye", "tuerkei", "turkei",
    },
    "RU": {
        "ru", "rus", "russia", "russland", "russianfederation",
    },
    "UA": {
        "ua", "ukr", "ukraine", "ukraina",
    },
    "CN": {
        "cn", "chn", "china", "volksrepublikchina",
    },
    "JP": {
        "jp", "jpn", "japan",
    },
    "KR": {
        "kr", "kor", "southkorea", "korea", "sudkorea", "republicofkorea",
    },
    "IN": {
        "in", "ind", "india", "indien",
    },
    "AU": {
        "au", "aus", "australia", "australien",
    },
    "NZ": {
        "nz", "nzl", "newzealand", "neuseeland",
    },
    "ZA": {
        "za", "zaf", "southafrica", "southafrica", "sudafrika",
    },
    "AE": {
        "ae", "are", "unitedarabemirates", "uae", "vereinigtearabischeemirate",
    },
    "SA": {
        "sa", "sau", "saudiarabia", "saudiarabien",
    },
    "IL": {
        "il", "isr", "israel",
    },
}

normalized_alias_to_code = {}
for code, aliases in country_aliases.items():
    for alias in aliases:
        normalized_alias_to_code[normalize_country_value(alias)] = code


def country_to_iso2(value):
    normalized_value = normalize_country_value(value)

    if normalized_value is None:
        return "UNKNOWN"

    if normalized_value in normalized_alias_to_code:
        return normalized_alias_to_code[normalized_value]

    # Für leichte Tippfehler wird nur dann eine Fuzzy-Zuordnung verwendet,
    # wenn der beste Treffer ausreichend ähnlich und eindeutig besser als
    # alle Alternativen ist.
    candidates = []
    for alias, code in normalized_alias_to_code.items():
        similarity = SequenceMatcher(None, normalized_value, alias).ratio()
        candidates.append((similarity, code))

    candidates.sort(reverse=True)
    best_similarity, best_code = candidates[0]
    second_similarity = candidates[1][0] if len(candidates) > 1 else 0

    if best_similarity >= 0.88 and (best_similarity - second_similarity) >= 0.05:
        return best_code

    return "UNKNOWN"


customers["country_code"] = customers["country"].map(country_to_iso2)

# Schritt 4: Doppelte Kundenschlüssel entfernen und entsprechend der Vorgabe
# stets das erste Vorkommen eines customer_id beibehalten.
customers = customers.drop_duplicates(subset=["customer_id"], keep="first")

# Schritt 5: Preisangaben aus den Produktdaten robust in numerische Float-Werte
# überführen; dabei werden Währungstexte sowie europäische Tausender-/Dezimalformate
# berücksichtigt.
def parse_eur_price(value):
    if pd.isna(value):
        return float("nan")

    text = str(value).strip()
    text = re.sub(r"[^\d,.\-]", "", text)

    if not text or text in {"-", ".", ","}:
        return float("nan")

    if "," in text and "." in text:
        # Das zuletzt vorkommende Trennzeichen wird als Dezimaltrennzeichen behandelt.
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")

    return pd.to_numeric(text, errors="coerce")


products["price_eur"] = products["price_eur"].map(parse_eur_price).astype(float)

# Schritt 6: Lagerbestandswerte in echte boolesche Werte konvertieren.
def parse_boolean(value):
    if pd.isna(value):
        return pd.NA

    if isinstance(value, bool):
        return value

    normalized_value = str(value).strip().casefold()
    true_values = {"true", "1", "yes", "y", "ja", "j", "in stock", "instock", "available"}
    false_values = {"false", "0", "no", "n", "nein", "out of stock", "outofstock", "unavailable"}

    if normalized_value in true_values:
        return True
    if normalized_value in false_values:
        return False
    return pd.NA


products["in_stock"] = products["in_stock"].map(parse_boolean).astype("boolean")

# Schritt 7: Bestellungen mit Kunden- und Produktdaten per Left Join verknüpfen,
# damit sämtliche Bestellzeilen erhalten bleiben.
customers_for_merge = customers[["customer_id", "country_code"]]
products_for_merge = products[["product_id", "category"]]

enriched_orders = orders.merge(
    customers_for_merge,
    on="customer_id",
    how="left",
    validate="m:1",
)

enriched_orders = enriched_orders.merge(
    products_for_merge,
    on="product_id",
    how="left",
    validate="m:1",
)

# Nicht aufgelöste Fremdschlüssel erhalten Gruppierungswerte, damit auch diese
# Bestellzeilen in der Umsatzauswertung erhalten bleiben.
enriched_orders["country_code"] = enriched_orders["country_code"].fillna("UNKNOWN")
enriched_orders["category"] = enriched_orders["category"].fillna("UNKNOWN")

# Schritt 8: Mengen und Bestellpreise numerisch machen und den Zeilenumsatz
# ausschließlich aus quantity und unit_price_eur der Bestellungen berechnen.
enriched_orders["quantity"] = pd.to_numeric(
    enriched_orders["quantity"], errors="coerce"
)
enriched_orders["unit_price_eur"] = enriched_orders["unit_price_eur"].map(
    parse_eur_price
)
enriched_orders["line_revenue_eur"] = (
    enriched_orders["quantity"] * enriched_orders["unit_price_eur"]
)

# Schritt 9: Umsatz je Land und Kategorie aggregieren. Wenn eine order_id
# existiert, werden eindeutige Bestellungen gezählt; andernfalls Bestellzeilen.
group_keys = ["country_code", "category"]

revenue = (
    enriched_orders.groupby(group_keys, dropna=False)["line_revenue_eur"]
    .sum(min_count=1)
    .reset_index(name="total_revenue_eur")
)

if "order_id" in enriched_orders.columns:
    order_counts = (
        enriched_orders.groupby(group_keys, dropna=False)["order_id"]
        .nunique()
        .reset_index(name="order_count")
    )
else:
    order_counts = (
        enriched_orders.groupby(group_keys, dropna=False)
        .size()
        .reset_index(name="order_count")
    )

result = revenue.merge(order_counts, on=group_keys, how="left")
result["total_revenue_eur"] = result["total_revenue_eur"].fillna(0).round(2)
result["order_count"] = result["order_count"].astype("int64")
result = result.sort_values(
    by="total_revenue_eur",
    ascending=False,
    kind="stable",
).reset_index(drop=True)

# Schritt 10: Zielverzeichnis anlegen und die fertige Umsatzauswertung
# als Parquet-Datei am exakt vorgegebenen Pfad speichern.
os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)