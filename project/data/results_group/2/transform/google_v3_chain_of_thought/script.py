# Step 1: Define file paths and load raw data
import os
import pandas as pd

products_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv"
orders_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/orders_raw.csv"
customers_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_hard/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_group/2/transform/google_v3_chain_of_thought/output.parquet"

products_df = pd.read_csv(products_path)
orders_df = pd.read_csv(orders_path)
customers_df = pd.read_parquet(customers_path)

# Transformation Step 1: Clean and convert price_eur to float and in_stock to boolean
# Remove currency symbols/text, strip spaces, replace comma with dot, convert to float
products_df['price_eur'] = (
    products_df['price_eur']
    .astype(str)
    .str.replace('€', '', regex=False)
    .str.replace('EUR', '', regex=False)
    .str.strip()
    .str.replace(',', '.', regex=False)
)
products_df['price_eur'] = pd.to_numeric(products_df['price_eur'], errors='coerce')

# Map string representations of booleans in in_stock
bool_mapping = {
    'ja': True, 'nein': False,
    'true': True, 'false': False,
    '1': True, '0': False
}
products_df['in_stock'] = (
    products_df['in_stock']
    .astype(str)
    .str.strip()
    .str.lower()
    .map(bool_mapping)
    .astype('boolean')
)

# Transformation Step 2: Calculate total_eur and extract year/month from ordered_at in orders
orders_df['total_eur'] = orders_df['quantity'] * orders_df['unit_price_eur']

ordered_at_dt = pd.to_datetime(orders_df['ordered_at'], errors='coerce')
orders_df['order_year'] = ordered_at_dt.dt.year.astype('Int64')
orders_df['order_month'] = ordered_at_dt.dt.month.astype('Int64')

# Transformation Step 3: Join datasets, aggregate per country_code & category, sort and save
# Inner join orders with products and customers (discarding unmapped orders)
merged_df = orders_df.merge(products_df, on='product_id', how='inner').merge(customers_df, on='customer_id', how='inner')

# Assign ISO country code from customer country
merged_df['country_code'] = merged_df['country']

# Filter out rows with missing or empty country_code or category
valid_mask = (
    merged_df['country_code'].notna() & 
    (merged_df['country_code'].astype(str).str.strip() != '') &
    merged_df['category'].notna() & 
    (merged_df['category'].astype(str).str.strip() != '')
)
merged_df = merged_df[valid_mask]

# Aggregate total revenue and count of orders
result_df = merged_df.groupby(['country_code', 'category'], as_index=False).agg(
    total_revenue_eur=('total_eur', 'sum'),
    order_count=('order_id', 'count')
)

# Sort descending by total_revenue_eur
result_df = result_df.sort_values(by='total_revenue_eur', ascending=False).reset_index(drop=True)

# Save result to specified Parquet output file
os.makedirs(os.path.dirname(output_path), exist_ok=True)
result_df.to_parquet(output_path, index=False)