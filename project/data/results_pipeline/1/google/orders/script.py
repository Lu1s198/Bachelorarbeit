import os
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/orders_raw.csv"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/orders/output.parquet"

os.makedirs(os.path.dirname(output_path), exist_ok=True)

df = pd.read_csv(input_path)
df["total_eur"] = df["quantity"] * df["unit_price_eur"]

ordered_at_dt = pd.to_datetime(df["ordered_at"])
df["order_year"] = ordered_at_dt.dt.year.astype("int64")
df["order_month"] = ordered_at_dt.dt.month.astype("int64")

df.to_parquet(output_path, index=False)