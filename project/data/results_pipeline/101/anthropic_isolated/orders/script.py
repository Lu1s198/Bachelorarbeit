import pandas as pd
import os

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/101/orders_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/anthropic_isolated/orders/output.parquet"

df = pd.read_csv(input_path, dtype={
    "order_id": "int64",
    "customer_id": "int64",
    "product_id": "int64",
    "quantity": "int64",
    "unit_price_eur": "float64",
    "ordered_at": "str"
})

df["total_eur"] = df["quantity"] * df["unit_price_eur"]

ordered_at_dt = pd.to_datetime(df["ordered_at"])
df["order_year"] = ordered_at_dt.dt.year.astype("int64")
df["order_month"] = ordered_at_dt.dt.month.astype("int64")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)