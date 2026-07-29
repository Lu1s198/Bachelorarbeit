import pandas as pd
import numpy as np

# Load data from CSV file
df = pd.read_csv('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/orders_raw.csv')

# Convert ordered_at to datetime and extract year and month
df['ordered_at'] = pd.to_datetime(df['ordered_at'])
df['order_year'] = df['ordered_at'].dt.year
df['order_month'] = df['ordered_at'].dt.month

# Calculate total_eur
df['total_eur'] = df['quantity'] * df['unit_price_eur']

# Ensure key columns are of the same type
df['order_id'] = pd.to_numeric(df['order_id'], errors='coerce')
df['customer_id'] = pd.to_numeric(df['customer_id'], errors='coerce')
df['product_id'] = pd.to_numeric(df['product_id'], errors='coerce')

# Write result to Parquet file
df[['order_id', 'customer_id', 'product_id', 'quantity', 'unit_price_eur', 'ordered_at', 'total_eur', 'order_year', 'order_month']].to_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama/orders/output.parquet', index=False)