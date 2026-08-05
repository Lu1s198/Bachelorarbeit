import pandas as pd
import os

df = pd.read_csv("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/orders_raw.csv")

df['ordered_at'] = pd.to_datetime(df['ordered_at'])
df['total_eur'] = df['quantity'] * df['unit_price_eur']
df['order_year'] = df['ordered_at'].dt.year.astype('int64')
df['order_month'] = df['ordered_at'].dt.month.astype('int64')

os.makedirs("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/orders", exist_ok=True)
df.to_parquet("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/orders/output.parquet", index=False)