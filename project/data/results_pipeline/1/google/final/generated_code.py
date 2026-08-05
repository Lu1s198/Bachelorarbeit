import os
import pandas as pd

customers_file = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/dedup_hard/output.parquet"
products_file = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/products/output.parquet"
orders_file = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/orders/output.parquet"
output_file = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/final/output.parquet"

customers = pd.read_parquet(customers_file)
products = pd.read_parquet(products_file)
orders = pd.read_parquet(orders_file)

if 'country_code' not in customers.columns and 'country' in customers.columns:
    customers['country_code'] = customers['country']

if 'customer_id' in orders.columns and 'customer_id' in customers.columns:
    if orders['customer_id'].dtype != customers['customer_id'].dtype:
        orders['customer_id'] = orders['customer_id'].astype(str)
        customers['customer_id'] = customers['customer_id'].astype(str)

if 'product_id' in orders.columns and 'product_id' in products.columns:
    if orders['product_id'].dtype != products['product_id'].dtype:
        orders['product_id'] = orders['product_id'].astype(str)
        products['product_id'] = products['product_id'].astype(str)

merged = orders.merge(customers, on='customer_id', how='inner')
merged = merged.merge(products, on='product_id', how='inner')

if 'unit_price_eur' not in merged.columns:
    if 'unit_price_eur_x' in merged.columns:
        merged['unit_price_eur'] = merged['unit_price_eur_x']
    elif 'unit_price_eur_y' in merged.columns:
        merged['unit_price_eur'] = merged['unit_price_eur_y']

merged['calculated_revenue'] = merged['quantity'] * merged['unit_price_eur']

if 'order_id' in merged.columns:
    result = merged.groupby(['country_code', 'category'], as_index=False).agg(
        total_revenue_eur=('calculated_revenue', 'sum'),
        order_count=('order_id', 'nunique')
    )
else:
    result = merged.groupby(['country_code', 'category'], as_index=False).agg(
        total_revenue_eur=('calculated_revenue', 'sum'),
        order_count=('customer_id', 'count')
    )

result = result.sort_values(by='total_revenue_eur', ascending=False).reset_index(drop=True)

os.makedirs(os.path.dirname(output_file), exist_ok=True)
result.to_parquet(output_file, index=False)