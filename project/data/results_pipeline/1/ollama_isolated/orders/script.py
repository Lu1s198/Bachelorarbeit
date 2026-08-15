import pandas as pd
import numpy as np

# Read input data
df = pd.read_csv('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/orders_raw.csv')

# Convert ordered_at to datetime
df['ordered_at'] = pd.to_datetime(df['ordered_at'])

# Extract year and month from ordered_at
df['order_year'] = df['ordered_at'].dt.year
df['order_month'] = df['ordered_at'].dt.month

# Calculate total_eur
df['total_eur'] = df['quantity'] * df['unit_price_eur']

# Ensure key columns are of the same type
df['order_id'] = df['order_id'].astype(np.int64)
df['customer_id'] = df['customer_id'].astype(np.int64)
df['product_id'] = df['product_id'].astype(np.int64)

# Write result to Parquet file
df.to_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama_isolated/orders/output.parquet', index=False)