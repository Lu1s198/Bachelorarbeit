import pandas as pd
import os

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/orders_raw.csv"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r4/orders/output.parquet"

df = pd.read_csv(input_path)

df["total_eur"] = df["quantity"] * df["unit_price_eur"]

parsed_dates = pd.to_datetime(df["ordered_at"], errors="coerce")
df["order_year"] = parsed_dates.dt.year.astype("Int64")
df["order_month"] = parsed_dates.dt.month.astype("Int64")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)