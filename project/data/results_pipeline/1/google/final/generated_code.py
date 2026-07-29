import os
import pandas as pd

customers_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/dedup_hard/output.parquet"
products_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/products/output.parquet"
orders_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/orders/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/final/output.parquet"

customers = pd.read_parquet(customers_path)
products = pd.read_parquet(products_path)
orders = pd.read_parquet(orders_path)

if 'country' in customers.columns:
    customers['country_code'] = customers['country']

def normalize_key(s):
    return s.astype(str).str.replace(r'\.0$', '', regex=True)

orders['customer_id'] = normalize_key(orders['customer_id'])
customers['customer_id'] = normalize_key(customers['customer_id'])

orders['product_id'] = normalize_key(orders['product_id'])
products['product_id'] = normalize_key(products['product_id'])

merged = orders.merge(customers, on='customer_id', how='inner')
merged = merged.merge(products, on='product_id', how='inner')

merged['quantity'] = pd.to_numeric(merged['quantity'], errors='coerce').fillna(0)
merged['unit_price_eur'] = pd.to_numeric(merged['unit_price_eur'], errors='coerce').fillna(0)
merged['revenue_item'] = merged['quantity'] * merged['unit_price_eur']

if 'order_id' in merged.columns:
    agg_dict = {
        'revenue_item': 'sum',
        'order_id': 'nunique'
    }
    rename_dict = {'revenue_item': 'total_revenue_eur', 'order_id': 'order_count'}
elif 'order_number' in merged.columns:
    agg_dict = {
        'revenue_item': 'sum',
        'order_number': 'nunique'
    }
    rename_dict = {'revenue_item': 'total_revenue_eur', 'order_number': 'order_count'}
else:
    agg_dict = {
        'revenue_item': 'sum',
        'customer_id': 'count'
    }
    rename_dict = {'revenue_item': 'total_revenue_eur', 'customer_id': 'order_count'}

result = (
    merged.groupby(['country_code', 'category'], as_index=False)
    .agg(agg_dict)
    .rename(columns=rename_dict)
)

result = result.sort_values(by='total_revenue_eur', ascending=False).reset_index(drop=True)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)