import pandas as pd
import numpy as np
import os

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/orders_raw.csv"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/orders/output.parquet"

df = pd.read_csv(input_path)

df['ordered_at'] = pd.to_datetime(df['ordered_at'], errors='coerce')
df['total_eur'] = df['quantity'] * df['unit_price_eur']
df['order_year'] = df['ordered_at'].dt.year.astype('Int64')
df['order_month'] = df['ordered_at'].dt.month.astype('Int64')

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)