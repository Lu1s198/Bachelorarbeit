# Step 1: Import required libraries and load raw datasets
import os
import re
import pandas as pd

# Define input directory and target output parquet file path
input_dir = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_composite/2/codegen/google_v3_chain_of_thought/output.parquet"

# Ensure output directory exists
os.makedirs(os.path.dirname(output_path), exist_ok=True)

# Load raw CSV datasets
customers_df = pd.read_csv(os.path.join(input_dir, "customers_raw.csv"))
products_df = pd.read_csv(os.path.join(input_dir, "products_raw.csv"))
orders_df = pd.read_csv(os.path.join(input_dir, "orders_raw.csv"))

# Sub-step 1: Remove leading and trailing whitespace from all text columns in customers_raw.csv
for col in customers_df.columns:
    if customers_df[col].dtype == "object" or isinstance(customers_df[col].dtype, pd.StringDtype):
        customers_df[col] = customers_df[col].astype(str).str.strip()

# Sub-step 2: Standardize country column in customers_raw.csv to 2-letter ISO-3166-1-alpha-2 code (country_code)
def standardize_country(val):
    if pd.isna(val) or str(val).strip().lower() in ["nan", "none", "null", ""]:
        return "UNKNOWN"
    
    val_clean = str(val).strip().upper()
    
    # Exact mappings for standard country names, abbreviations, and common typos
    mapping = {
        "DE": ["DE", "GER", "DEU", "DEUTSCHLAND", "GERMANY", "DEUTSHCLAND", "BUNDESREPUBLIK DEUTSCHLAND"],
        "AT": ["AT", "AUT", "AUSTRIA", "ÖSTERREICH", "OESTERREICH", "OSTERREICH"],
        "CH": ["CH", "CHE", "SWITZERLAND", "SCHWEIZ", "SUISSE", "SVIZZERA"],
        "FR": ["FR", "FRA", "FRANCE", "FRANKREICH"],
        "US": ["US", "USA", "UNITED STATES", "UNITED STATES OF AMERICA"],
        "GB": ["GB", "UK", "GBR", "UNITED KINGDOM", "GREAT BRITAIN", "GROSSBRITANNIEN", "ENGLAND"],
        "IT": ["IT", "ITA", "ITALY", "ITALIEN"],
        "ES": ["ES", "ESP", "SPAIN", "SPANIEN"],
        "NL": ["NL", "NLD", "NETHERLANDS", "NIEDERLANDE"],
        "PL": ["PL", "POL", "POLAND", "POLEN"]
    }
    
    for iso_code, variations in mapping.items():
        if val_clean in variations:
            return iso_code
            
    # Regex fallback for minor typo patterns
    if re.search(r"DEUT|GERM", val_clean):
        return "DE"
    if re.search(r"ÖST|OEST|AUST", val_clean):
        return "AT"
    if re.search(r"SCHW|SWIT", val_clean):
        return "CH"
    if re.search(r"FRAN|FREN", val_clean):
        return "FR"
    if re.search(r"SPAN|SPAI", val_clean):
        return "ES"
    if re.search(r"ITAL", val_clean):
        return "IT"

    return "UNKNOWN"

customers_df["country_code"] = customers_df["country"].apply(standardize_country)

# Sub-step 3: Remove records with duplicate customer_id from customers_raw.csv, keeping the first occurrence
customers_df = customers_df.drop_duplicates(subset=["customer_id"], keep="first")

# Sub-step 4: Convert price_eur in products_raw.csv to float and in_stock to boolean
def parse_price(val):
    if pd.isna(val):
        return None
    val_str = str(val).upper().replace("EUR", "").replace("€", "").strip().replace(",", ".")
    try:
        return float(val_str)
    except ValueError:
        return None

products_df["price_eur"] = products_df["price_eur"].apply(parse_price)

def parse_boolean(val):
    if pd.isna(val):
        return False
    val_str = str(val).strip().lower()
    return val_str in ["true", "1", "ja", "yes", "t", "y", "wahr"]

products_df["in_stock"] = products_df["in_stock"].apply(parse_boolean)

# Sub-step 5: Join orders_raw.csv with customers_raw.csv (customer_id) and products_raw.csv (product_id)
# Keeping all order lines from orders_raw.csv (left join)
merged_df = orders_df.merge(
    customers_df[["customer_id", "country_code"]],
    on="customer_id",
    how="left"
).merge(
    products_df[["product_id", "category"]],
    on="product_id",
    how="left"
)

# Handle unassigned missing country_code and category values
merged_df["country_code"] = merged_df["country_code"].fillna("UNKNOWN")
merged_df["category"] = merged_df["category"].fillna("UNKNOWN")

# Sub-step 6: Calculate revenue (quantity * unit_price_eur), aggregate per country_code and category, round, and sort
merged_df["line_revenue"] = merged_df["quantity"] * merged_df["unit_price_eur"]

aggregated_df = (
    merged_df.groupby(["country_code", "category"], as_index=False)
    .agg(
        total_revenue_eur=("line_revenue", "sum"),
        order_count=("quantity", "count")
    )
)

aggregated_df["total_revenue_eur"] = aggregated_df["total_revenue_eur"].round(2)
aggregated_df = aggregated_df.sort_values(by="total_revenue_eur", ascending=False).reset_index(drop=True)

# Write output to Parquet file
aggregated_df.to_parquet(output_path, index=False)