import os
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/orders_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/orders/output.parquet"

df = pd.read_csv(input_path)

df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
df["unit_price_eur"] = pd.to_numeric(df["unit_price_eur"], errors="coerce")
df["ordered_at"] = pd.to_datetime(df["ordered_at"], errors="coerce", format="mixed")

df["total_eur"] = df["quantity"] * df["unit_price_eur"]
df["order_year"] = df["ordered_at"].dt.year.astype("Int64")
df["order_month"] = df["ordered_at"].dt.month.astype("Int64")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)