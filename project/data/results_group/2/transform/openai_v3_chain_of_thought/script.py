import os
import re
import pandas as pd

# Sub-step 1: Define input/output paths and load the three source tables.
base_input = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2"
products_path = os.path.join(base_input, "products_raw.csv")
orders_path = os.path.join(base_input, "orders_raw.csv")
customers_path = (
    r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/"
    r"results_pipeline/2/_reference/dedup_hard/output.parquet"
)
output_path = (
    r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/"
    r"results_group/2/transform/openai_v3_chain_of_thought/output.parquet"
)

products = pd.read_csv(products_path)
orders = pd.read_csv(orders_path)
customers = pd.read_parquet(customers_path)

# Sub-step 2: Convert textual EUR prices into floats with a decimal point.
# The parser supports values such as "19,99", "€19.99", and "19.99 EUR".
def parse_eur_price(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype("string")
        .str.replace(r"[^\d,.\-]", "", regex=True)
        .str.strip()
    )

    # If both separators exist, treat the last separator as the decimal separator.
    both_separators = cleaned.str.contains(",", na=False) & cleaned.str.contains(".", na=False)
    comma_last = both_separators & (
        cleaned.str.rfind(",") > cleaned.str.rfind(".")
    )

    normalized = cleaned.copy()
    normalized.loc[comma_last] = (
        normalized.loc[comma_last]
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    normalized.loc[both_separators & ~comma_last] = (
        normalized.loc[both_separators & ~comma_last]
        .str.replace(",", "", regex=False)
    )

    # With only a comma present, it is interpreted as the decimal separator.
    comma_only = normalized.str.contains(",", na=False) & ~normalized.str.contains(".", na=False)
    normalized.loc[comma_only] = normalized.loc[comma_only].str.replace(",", ".", regex=False)

    return pd.to_numeric(normalized, errors="coerce")

products["price_eur"] = parse_eur_price(products["price_eur"])

# Sub-step 3: Convert supported stock text representations into nullable booleans.
stock_values = products["in_stock"].astype("string").str.strip().str.lower()
products["in_stock"] = stock_values.map(
    {
        "ja": True,
        "yes": True,
        "true": True,
        "1": True,
        "nein": False,
        "no": False,
        "false": False,
        "0": False,
    }
).astype("boolean")

# Sub-step 4: Calculate order totals and extract year/month from the order timestamp.
orders["total_eur"] = orders["quantity"] * orders["unit_price_eur"]
orders["ordered_at"] = pd.to_datetime(orders["ordered_at"], errors="coerce")
orders["order_year"] = orders["ordered_at"].dt.year.astype("Int64")
orders["order_month"] = orders["ordered_at"].dt.month.astype("Int64")

# Sub-step 5: Prepare customer country values as the requested country_code.
customers = customers.copy()
customers["country_code"] = customers["country"].astype("string").str.strip()

# Sub-step 6: Keep only valid country/category dimension values before joining.
valid_customers = customers.loc[
    customers["country_code"].notna() & customers["country_code"].ne(""),
    ["customer_id", "country_code"],
]
valid_products = products.loc[
    products["category"].notna() & products["category"].astype("string").str.strip().ne(""),
    ["product_id", "category"],
].copy()
valid_products["category"] = valid_products["category"].astype("string").str.strip()

# Sub-step 7: Inner joins intentionally exclude orders lacking a matching customer or product.
enriched_orders = (
    orders.merge(valid_customers, on="customer_id", how="inner", validate="many_to_one")
    .merge(valid_products, on="product_id", how="inner", validate="many_to_one")
)

# Sub-step 8: Aggregate revenue and order count by country and product category, then sort.
result = (
    enriched_orders.groupby(["country_code", "category"], as_index=False, dropna=True)
    .agg(
        total_revenue_eur=("total_eur", "sum"),
        order_count=("order_id", "count"),
    )
    .sort_values(
        ["total_revenue_eur", "country_code", "category"],
        ascending=[False, True, True],
        kind="stable",
    )
    .reset_index(drop=True)
)

# Sub-step 9: Create the destination directory and write only the final transformation result.
os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)