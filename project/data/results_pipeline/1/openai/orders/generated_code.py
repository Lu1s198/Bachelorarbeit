import os
import pandas as pd
import numpy as np

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/orders_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/orders/output.parquet"

df = pd.read_csv(input_path)

required_columns = [
    "order_id",
    "customer_id",
    "product_id",
    "quantity",
    "unit_price_eur",
    "ordered_at",
]

missing_columns = [column for column in required_columns if column not in df.columns]
if missing_columns:
    raise ValueError(f"Missing required columns: {missing_columns}")

df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
df["unit_price_eur"] = pd.to_numeric(df["unit_price_eur"], errors="coerce")
df["total_eur"] = df["quantity"] * df["unit_price_eur"]

ordered_at_parsed = pd.to_datetime(df["ordered_at"], errors="coerce", format="mixed")
df["order_year"] = ordered_at_parsed.dt.year.astype("Int64")
df["order_month"] = ordered_at_parsed.dt.month.astype("Int64")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)