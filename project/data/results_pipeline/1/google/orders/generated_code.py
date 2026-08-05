import os
import pandas as pd

input_file = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/orders_raw.csv"
output_file = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/orders/output.parquet"

df = pd.read_csv(input_file)

df["total_eur"] = df["quantity"] * df["unit_price_eur"]

ordered_at_dt = pd.to_datetime(df["ordered_at"])
df["order_year"] = ordered_at_dt.dt.year.astype(int)
df["order_month"] = ordered_at_dt.dt.month.astype(int)

os.makedirs(os.path.dirname(output_file), exist_ok=True)
df.to_parquet(output_file, index=False)