import os
import pandas as pd

customers_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google/dedup_hard/output.parquet"
products_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google/products/output.parquet"
orders_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google/orders/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google/final/output.parquet"

customers = pd.read_parquet(customers_path)
products = pd.read_parquet(products_path)
orders = pd.read_parquet(orders_path)

customers['customer_id'] = customers['customer_id'].astype('int64')
orders['customer_id'] = orders['customer_id'].astype('int64')
products['product_id'] = products['product_id'].astype('int64')
orders['product_id'] = orders['product_id'].astype('int64')

merged = orders.merge(customers, on='customer_id', how='inner')
merged = merged.merge(products, on='product_id', how='inner')

merged['country_code'] = merged['country']

merged = merged[merged['country_code'].notna() & (merged['country_code'] != '')]
merged = merged[merged['category'].notna() & (merged['category'] != '')]

merged['calculated_total'] = merged['quantity'] * merged['unit_price_eur']

res = merged.groupby(['country_code', 'category'], as_index=False).agg(
    total_revenue_eur=('calculated_total', 'sum'),
    order_count=('order_id', 'count')
)

res = res.sort_values(by='total_revenue_eur', ascending=False).reset_index(drop=True)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
res.to_parquet(output_path, index=False)