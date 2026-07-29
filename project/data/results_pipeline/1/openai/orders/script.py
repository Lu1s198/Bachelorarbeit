import os
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/orders_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/orders/output.parquet"

df = pd.read_csv(input_path)

df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
df["unit_price_eur"] = pd.to_numeric(df["unit_price_eur"], errors="coerce")
df["ordered_at"] = pd.to_datetime(df["ordered_at"], errors="coerce")

df["total_eur"] = df["quantity"] * df["unit_price_eur"]
df["order_year"] = df["ordered_at"].dt.year.astype("Int64")
df["order_month"] = df["ordered_at"].dt.month.astype("Int64")

required_columns = [
    "order_id",
    "customer_id",
    "product_id",
    "quantity",
    "unit_price_eur",
    "ordered_at",
    "total_eur",
    "order_year",
    "order_month",
]
df = df[[col for col in required_columns if col in df.columns] + [
    col for col in df.columns if col not in required_columns
]]

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)