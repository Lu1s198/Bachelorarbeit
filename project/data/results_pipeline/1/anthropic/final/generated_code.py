import pandas as pd
import numpy as np
import os

customers_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/dedup_hard/output.parquet"
products_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/products/output.parquet"
orders_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/orders/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/final/output.parquet"

customers = pd.read_parquet(customers_path)
products = pd.read_parquet(products_path)
orders = pd.read_parquet(orders_path)

customers['customer_id'] = customers['customer_id'].astype(str)
orders['customer_id'] = orders['customer_id'].astype(str)

products['product_id'] = products['product_id'].astype(str)
orders['product_id'] = orders['product_id'].astype(str)

customers['country_code'] = customers['country']

merged = orders.merge(customers[['customer_id', 'country_code']], on='customer_id', how='inner')
merged = merged.merge(products[['product_id', 'category']], on='product_id', how='inner')

merged = merged.dropna(subset=['country_code', 'category'])
merged = merged[merged['country_code'].astype(str).str.strip() != '']
merged = merged[merged['category'].astype(str).str.strip() != '']

merged['quantity'] = pd.to_numeric(merged['quantity'], errors='coerce')
merged['unit_price_eur'] = pd.to_numeric(merged['unit_price_eur'], errors='coerce')

merged['revenue'] = merged['quantity'] * merged['unit_price_eur']

result = merged.groupby(['country_code', 'category'], as_index=False).agg(
    total_revenue_eur=('revenue', 'sum'),
    order_count=('revenue', 'count')
)

result = result.sort_values('total_revenue_eur', ascending=False).reset_index(drop=True)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)