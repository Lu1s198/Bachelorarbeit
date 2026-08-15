import os
import pandas as pd

customers_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/_reference/dedup_hard/output.parquet"
products_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/_reference/products/output.parquet"
orders_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/_reference/orders/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/google_isolated/final/output.parquet"

customers = pd.read_parquet(customers_path)
products = pd.read_parquet(products_path)
orders = pd.read_parquet(orders_path)

customers['customer_id'] = customers['customer_id'].astype('int64')
products['product_id'] = products['product_id'].astype('int64')
orders['customer_id'] = orders['customer_id'].astype('int64')
orders['product_id'] = orders['product_id'].astype('int64')

merged = orders.merge(customers, on='customer_id', how='inner')
merged = merged.merge(products, on='product_id', how='inner')

merged['country_code'] = merged['country']

valid_mask = (
    merged['country_code'].notna() & 
    (merged['country_code'].astype(str).str.strip() != '') & 
    merged['category'].notna() & 
    (merged['category'].astype(str).str.strip() != '')
)
merged = merged[valid_mask]

merged['line_total'] = merged['quantity'] * merged['unit_price_eur']

aggregated = merged.groupby(['country_code', 'category'], as_index=False).agg(
    total_revenue_eur=('line_total', 'sum'),
    order_count=('order_id', 'count')
)

aggregated = aggregated.sort_values(by='total_revenue_eur', ascending=False).reset_index(drop=True)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
aggregated.to_parquet(output_path, index=False)