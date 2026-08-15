import os
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/101/orders_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/openai/orders/output.parquet"

df = pd.read_csv(input_path)

df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
df["unit_price_eur"] = pd.to_numeric(df["unit_price_eur"], errors="coerce")
df["total_eur"] = df["quantity"] * df["unit_price_eur"]

ordered_at_datetime = pd.to_datetime(df["ordered_at"], errors="coerce")
df["order_year"] = ordered_at_datetime.dt.year.astype("Int64")
df["order_month"] = ordered_at_datetime.dt.month.astype("Int64")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)