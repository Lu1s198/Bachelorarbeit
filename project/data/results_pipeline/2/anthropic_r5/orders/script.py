import pandas as pd
import os

df = pd.read_csv("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/orders_raw.csv")

df['total_eur'] = df['quantity'] * df['unit_price_eur']

parsed = pd.to_datetime(df['ordered_at'], errors='coerce')
df['order_year'] = parsed.dt.year.astype('Int64')
df['order_month'] = parsed.dt.month.astype('Int64')

output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r5/orders/output.parquet"
os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)