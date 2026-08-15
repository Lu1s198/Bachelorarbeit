import os
import pandas as pd

customers_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_hard/output.parquet"
products_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/products/output.parquet"
orders_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/orders/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_isolated_r2/final/output.parquet"

df_customers = pd.read_parquet(customers_path)
df_products = pd.read_parquet(products_path)
df_orders = pd.read_parquet(orders_path)

df_customers['customer_id'] = df_customers['customer_id'].astype('int64')
df_products['product_id'] = df_products['product_id'].astype('int64')
df_orders['customer_id'] = df_orders['customer_id'].astype('int64')
df_orders['product_id'] = df_orders['product_id'].astype('int64')

df_merged = df_orders.merge(df_customers, on='customer_id', how='inner')
df_merged = df_merged.merge(df_products, on='product_id', how='inner')

df_merged['country_code'] = df_merged['country']
df_merged['line_total'] = df_merged['quantity'] * df_merged['unit_price_eur']

df_merged = df_merged[df_merged['country_code'].notna() & df_merged['category'].notna()]
df_merged = df_merged[(df_merged['country_code'].astype(str).str.strip() != '') & (df_merged['category'].astype(str).str.strip() != '')]

df_agg = df_merged.groupby(['country_code', 'category'], as_index=False).agg(
    total_revenue_eur=('line_total', 'sum'),
    order_count=('order_id', 'count')
)

df_agg = df_agg.sort_values(by='total_revenue_eur', ascending=False).reset_index(drop=True)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df_agg.to_parquet(output_path, index=False)