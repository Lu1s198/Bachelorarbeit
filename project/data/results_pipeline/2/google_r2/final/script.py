import os
import pandas as pd

customers_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r2/dedup_hard/output.parquet"
products_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r2/products/output.parquet"
orders_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r2/orders/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r2/final/output.parquet"

customers = pd.read_parquet(customers_path)
products = pd.read_parquet(products_path)
orders = pd.read_parquet(orders_path)

customers = customers.rename(columns={'country': 'country_code'})

orders['customer_id'] = orders['customer_id'].astype(customers['customer_id'].dtype)
orders['product_id'] = orders['product_id'].astype(products['product_id'].dtype)

orders['line_revenue'] = orders['quantity'] * orders['unit_price_eur']

merged = orders.merge(customers[['customer_id', 'country_code']], on='customer_id', how='inner')
merged = merged.merge(products[['product_id', 'category']], on='product_id', how='inner')

merged = merged[merged['country_code'].notna() & (merged['country_code'].astype(str).str.strip() != '')]
merged = merged[merged['category'].notna() & (merged['category'].astype(str).str.strip() != '')]

aggregated = merged.groupby(['country_code', 'category'], as_index=False).agg(
    total_revenue_eur=('line_revenue', 'sum'),
    order_count=('order_id', 'count')
)

aggregated = aggregated.sort_values(by='total_revenue_eur', ascending=False).reset_index(drop=True)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
aggregated.to_parquet(output_path, index=False)