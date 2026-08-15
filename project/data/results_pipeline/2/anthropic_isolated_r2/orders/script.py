import pandas as pd
import numpy as np
import os

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/orders_raw.csv"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_isolated_r2/orders/output.parquet"

df = pd.read_csv(input_path, dtype={
    "order_id": "int64",
    "customer_id": "int64",
    "product_id": "int64",
    "quantity": "int64",
    "unit_price_eur": "float64",
    "ordered_at": "str"
})

df["total_eur"] = df["quantity"] * df["unit_price_eur"]

parsed_dates = pd.to_datetime(df["ordered_at"], errors="coerce")
df["order_year"] = parsed_dates.dt.year.astype("Int64")
df["order_month"] = parsed_dates.dt.month.astype("Int64")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)