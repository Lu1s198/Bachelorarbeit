import pandas as pd
import numpy as np

# Load data from Parquet files
customers = pd.read_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama/dedup_hard/output.parquet')
products = pd.read_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama/products/output.parquet')
orders = pd.read_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama/orders/output.parquet')

# Merge data on customer_id and product_id
merged_data = customers.merge(orders, on='customer_id').merge(products, on='product_id')

# Map category to a more readable format (e.g., 'Electronics' instead of 'E')
category_map = {
    'E': 'Electronics',
    'F': 'Fashion',
    'H': 'Home Goods',
    'M': 'Music'
}
merged_data['category'] = merged_data['category'].map(category_map)

# Calculate total revenue in EUR
merged_data['total_revenue_eur'] = merged_data['quantity'] * merged_data['unit_price_eur']

# Group by country_code and category, aggregate and sort
result = (merged_data.groupby(['country_code', 'category'])
           ['total_revenue_eur', 'order_count'].sum().reset_index()
           .sort_values(by='total_revenue_eur', ascending=False))

# Write result to Parquet file
result.to_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama/final/output.parquet')