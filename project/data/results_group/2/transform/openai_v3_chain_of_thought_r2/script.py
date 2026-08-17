import os
import pandas as pd

# Schritt 1: Eingabedateien laden und die Produktspalten price_eur sowie in_stock bereinigen.
products_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv"
orders_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/orders_raw.csv"
customers_path = (
    r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/"
    r"_reference/dedup_hard/output.parquet"
)
output_path = (
    r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/"
    r"transform/openai_v3_chain_of_thought_r2/output.parquet"
)

products = pd.read_csv(products_path)
orders = pd.read_csv(orders_path)
customers = pd.read_parquet(customers_path)

# Preiswerte werden von Währungssymbolen/-bezeichnungen bereinigt und mit Dezimalpunkt in Float konvertiert.
def parse_eur_price(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype("string")
        .str.strip()
        .str.replace(r"(?i)\beur\b", "", regex=True)
        .str.replace("€", "", regex=False)
        .str.replace(r"\s+", "", regex=True)
    )

    # Bei Werten mit Punkt und Komma wird das jeweils letzte Trennzeichen als Dezimaltrennzeichen behandelt.
    both_separators = cleaned.str.contains(",", na=False) & cleaned.str.contains(r"\.", regex=True, na=False)
    comma_is_decimal = both_separators & (
        cleaned.str.rfind(",") > cleaned.str.rfind(".")
    )

    normalized = cleaned.copy()
    normalized.loc[comma_is_decimal] = (
        normalized.loc[comma_is_decimal]
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    normalized.loc[both_separators & ~comma_is_decimal] = (
        normalized.loc[both_separators & ~comma_is_decimal]
        .str.replace(",", "", regex=False)
    )

    # Werte mit ausschließlich Komma verwenden das Komma als Dezimaltrennzeichen.
    only_comma = normalized.str.contains(",", na=False) & ~normalized.str.contains(r"\.", regex=True, na=False)
    normalized.loc[only_comma] = normalized.loc[only_comma].str.replace(",", ".", regex=False)

    return pd.to_numeric(normalized, errors="coerce").astype("float64")


products["price_eur"] = parse_eur_price(products["price_eur"])

# Unterschiedliche deutsche und englische Boolesche Textdarstellungen werden auf einen Nullable-Boolean abgebildet.
stock_values = products["in_stock"].astype("string").str.strip().str.lower()
products["in_stock"] = stock_values.map(
    {
        "ja": True,
        "true": True,
        "1": True,
        "yes": True,
        "nein": False,
        "false": False,
        "0": False,
        "no": False,
    }
).astype("boolean")

# Schritt 2: Umsatz je Bestellzeile berechnen und Jahr/Monat aus dem Bestelldatum extrahieren.
orders["total_eur"] = orders["quantity"] * orders["unit_price_eur"]

ordered_at_datetime = pd.to_datetime(orders["ordered_at"], errors="coerce")
orders["order_year"] = ordered_at_datetime.dt.year.astype("Int64")
orders["order_month"] = ordered_at_datetime.dt.month.astype("Int64")

# Schritt 3: Bestellungen mit vorhandenen Kunden und Produkten verknüpfen, validieren und aggregieren.
customers_for_join = customers[["customer_id", "country"]].copy()
customers_for_join["country_code"] = customers_for_join["country"].astype("string").str.strip()

products_for_join = products[["product_id", "category"]].copy()
products_for_join["category"] = products_for_join["category"].astype("string").str.strip()

# Inner Joins stellen sicher, dass Bestellungen ohne passenden Kunden oder Produkt nicht berücksichtigt werden.
joined = (
    orders.merge(
        customers_for_join[["customer_id", "country_code"]],
        on="customer_id",
        how="inner",
        validate="many_to_one",
    )
    .merge(
        products_for_join,
        on="product_id",
        how="inner",
        validate="many_to_one",
    )
)

# Fehlende oder leere Länder- und Kategorieangaben werden vor der Aggregation ausgeschlossen.
valid_rows = (
    joined["country_code"].notna()
    & joined["category"].notna()
    & joined["country_code"].ne("")
    & joined["category"].ne("")
)
joined = joined.loc[valid_rows].copy()

# Der Umsatz wird summiert; die Bestellanzahl entspricht der Anzahl gültiger Bestellzeilen je Gruppe.
result = (
    joined.groupby(["country_code", "category"], as_index=False, dropna=False)
    .agg(
        total_revenue_eur=("total_eur", "sum"),
        order_count=("order_id", "count"),
    )
    .sort_values(
        by=["total_revenue_eur", "country_code", "category"],
        ascending=[False, True, True],
        kind="stable",
    )
    .reset_index(drop=True)
)

# Das Zielverzeichnis wird bei Bedarf angelegt und ausschließlich das Endergebnis als Parquet gespeichert.
os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)