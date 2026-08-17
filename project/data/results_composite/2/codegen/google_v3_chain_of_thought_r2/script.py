import os
import pandas as pd

# Define input and output file paths
input_dir = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_composite/2/codegen/google_v3_chain_of_thought_r2/output.parquet"

# Read raw datasets
customers_raw = pd.read_csv(os.path.join(input_dir, "customers_raw.csv"))
products_raw = pd.read_csv(os.path.join(input_dir, "products_raw.csv"))
orders_raw = pd.read_csv(os.path.join(input_dir, "orders_raw.csv"))

# Step 1: Strip leading and trailing whitespace from all text columns in customers_raw.csv
for col in customers_raw.select_dtypes(include=["object"]).columns:
    customers_raw[col] = customers_raw[col].astype(str).str.strip()

# Step 2: Harmonize the 'country' column in customers_raw.csv to ISO-3166-1-alpha-2 codes (country_code)
# Define mapping dictionary for common country names, abbreviations, and typos
country_mapping = {
    'deutschland': 'DE', 'germany': 'DE', 'ger': 'DE', 'deutshcland': 'DE', 'deutchland': 'DE', 'de': 'DE',
    'österreich': 'AT', 'oesterreich': 'AT', 'austria': 'AT', 'aut': 'AT', 'at': 'AT',
    'schweiz': 'CH', 'switzerland': 'CH', 'che': 'CH', 'ch': 'CH',
    'frankreich': 'FR', 'france': 'FR', 'fra': 'FR', 'fr': 'FR',
    'italien': 'IT', 'italy': 'IT', 'ita': 'IT', 'it': 'IT',
    'spanien': 'ES', 'spain': 'ES', 'esp': 'ES', 'es': 'ES',
    'niederlande': 'NL', 'netherlands': 'NL', 'nld': 'NL', 'nl': 'NL',
    'vereinigtes koenigreich': 'GB', 'vereinigtes königreich': 'GB', 'united kingdom': 'GB', 'uk': 'GB', 'gbr': 'GB', 'gb': 'GB',
    'usa': 'US', 'united states': 'US', 'united states of america': 'US', 'us': 'US'
}

def clean_country(val):
    if pd.isna(val) or val is None:
        return 'UNKNOWN'
    s = str(val).strip().lower()
    return country_mapping.get(s, 'UNKNOWN')

customers_raw['country_code'] = customers_raw['country'].apply(clean_country)

# Step 3: Remove duplicate customer_id in customers_raw.csv, keeping the first occurrence
customers_cleaned = customers_raw.drop_duplicates(subset=['customer_id'], keep='first')

# Step 4: Convert price_eur to float and in_stock to boolean in products_raw.csv
def parse_price(val):
    if pd.isna(val):
        return None
    s = str(val).replace('EUR', '').replace('eur', '').replace(',', '.').strip()
    try:
        return float(s)
    except ValueError:
        return None

def parse_bool(val):
    if pd.isna(val):
        return False
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    return s in ['true', '1', 't', 'yes', 'ja', 'wahr']

products_raw['price_eur'] = products_raw['price_eur'].apply(parse_price)
products_raw['in_stock'] = products_raw['in_stock'].apply(parse_bool)

# Step 5: Join orders_raw.csv with customers_cleaned on customer_id and products_raw on product_id
# All order rows from orders_raw.csv must be retained (left join)
merged_df = orders_raw.merge(customers_cleaned, on='customer_id', how='left')
merged_df = merged_df.merge(products_raw, on='product_id', how='left')

# Step 6: Calculate total revenue and order count aggregated by country_code and category
# total_revenue_eur = sum(quantity * unit_price_eur) using columns from orders_raw.csv
merged_df['revenue'] = merged_df['quantity'] * merged_df['unit_price_eur']

aggregated = merged_df.groupby(['country_code', 'category'], as_index=False).agg(
    total_revenue_eur=('revenue', 'sum'),
    order_count=('order_id', 'count')
)

# Round total_revenue_eur to two decimal places
aggregated['total_revenue_eur'] = aggregated['total_revenue_eur'].round(2)

# Sort descending by total_revenue_eur
aggregated = aggregated.sort_values(by='total_revenue_eur', ascending=False).reset_index(drop=True)

# Save result as Parquet file to the required directory
os.makedirs(os.path.dirname(output_path), exist_ok=True)
aggregated.to_parquet(output_path, index=False)