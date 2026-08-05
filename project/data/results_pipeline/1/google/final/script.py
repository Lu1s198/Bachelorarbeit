import os
import pandas as pd

customers_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/dedup_hard/output.parquet"
products_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/products/output.parquet"
orders_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/orders/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/final/output.parquet"

customers = pd.read_parquet(customers_path)
products = pd.read_parquet(products_path)
orders = pd.read_parquet(orders_path)

orders = orders.dropna(subset=['customer_id', 'product_id']).copy()
customers = customers.dropna(subset=['customer_id']).copy()
products = products.dropna(subset=['product_id']).copy()

orders['customer_id'] = orders['customer_id'].astype(str)
customers['customer_id'] = customers['customer_id'].astype(str)

orders['product_id'] = orders['product_id'].astype(str)
products['product_id'] = products['product_id'].astype(str)

merged = orders.merge(customers, on='customer_id', how='inner')
merged = merged.merge(products, on='product_id', how='inner')

if 'country_code' not in merged.columns and 'country' in merged.columns:
    merged['country_code'] = merged['country']

valid_mask = (
    merged['country_code'].notna() &
    (merged['country_code'].astype(str).str.strip() != '') &
    (merged['country_code'].astype(str).str.lower() != 'nan') &
    merged['category'].notna() &
    (merged['category'].astype(str).str.strip() != '') &
    (merged['category'].astype(str).str.lower() != 'nan')
)
merged = merged[valid_mask].copy()

if 'unit_price_eur' in merged.columns:
    unit_price = merged['unit_price_eur']
elif 'unit_price_eur_x' in merged.columns:
    unit_price = merged['unit_price_eur_x'].fillna(merged['unit_price_eur_y'])
elif 'unit_price_eur_y' in merged.columns:
    unit_price = merged['unit_price_eur_y']

if 'quantity' in merged.columns:
    quantity = merged['quantity']
elif 'quantity_x' in merged.columns:
    quantity = merged['quantity_x'].fillna(merged['quantity_y'])
elif 'quantity_y' in merged.columns:
    quantity = merged['quantity_y']

merged['revenue'] = quantity * unit_price

result = (
    merged.groupby(['country_code', 'category'], as_index=False)
    .agg(
        total_revenue_eur=('revenue', 'sum'),
        order_count=('revenue', 'count')
    )
    .sort_values(by='total_revenue_eur', ascending=False)
    .reset_index(drop=True)
)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)