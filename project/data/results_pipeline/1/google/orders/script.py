import os
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/orders_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/orders/output.parquet"

df = pd.read_csv(input_path)

df['total_eur'] = df['quantity'] * df['unit_price_eur']
df['ordered_at'] = pd.to_datetime(df['ordered_at'])
df['order_year'] = df['ordered_at'].dt.year.astype(int)
df['order_month'] = df['ordered_at'].dt.month.astype(int)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)