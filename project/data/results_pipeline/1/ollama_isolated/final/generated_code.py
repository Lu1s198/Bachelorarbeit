import pandas as pd
from numpy import nan

# Load data from Parquet files
customers = pd.read_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/_reference/dedup_hard/output.parquet')
products = pd.read_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/_reference/products/output.parquet')
orders = pd.read_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/_reference/orders/output.parquet')

# Ensure key columns are of the same type
customers['customer_id'] = customers['customer_id'].astype(int)
products['product_id'] = products['product_id'].astype(int)
orders['customer_id'] = orders['customer_id'].astype(int)
orders['product_id'] = orders['product_id'].astype(int)

# Merge data on customer and product IDs
merged_data = pd.merge(orders, customers[['customer_id', 'country']], how='left', left_on='customer_id', right_on='customer_id')
merged_data = pd.merge(merged_data, products[['product_id', 'category', 'price_eur']], how='left', left_on='product_id', right_on='product_id')

# Filter out rows with missing country or category
merged_data = merged_data.dropna(subset=['country', 'category'])

# Convert country to ISO code (assuming it's already in the correct format)
merged_data['country_code'] = merged_data['country']

# Calculate total revenue and order count
merged_data['total_revenue_eur'] = merged_data['quantity'] * merged_data['unit_price_eur']
merged_data['order_count'] = 1

# Group by country code and category, aggregate and sort
result = merged_data.groupby(['country_code', 'category'])[['total_revenue_eur', 'order_count']].sum().reset_index()
result = result.sort_values(by='total_revenue_eur', ascending=False)

# Write result to Parquet file
result.to_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama_isolated/final/output.parquet')