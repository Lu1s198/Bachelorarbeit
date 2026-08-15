import pandas as pd
import os

df = pd.read_csv("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/orders_raw.csv")

df["total_eur"] = df["quantity"] * df["unit_price_eur"]
df["ordered_at"] = pd.to_datetime(df["ordered_at"])
df["order_year"] = df["ordered_at"].dt.year.astype(int)
df["order_month"] = df["ordered_at"].dt.month.astype(int)

os.makedirs("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r3/orders", exist_ok=True)
df.to_parquet("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r3/orders/output.parquet", index=False)