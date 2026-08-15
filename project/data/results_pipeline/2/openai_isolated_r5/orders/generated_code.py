import os
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/orders_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_isolated_r5/orders/output.parquet"

df = pd.read_csv(input_path)

df["total_eur"] = df["quantity"] * df["unit_price_eur"]

ordered_datetime = pd.to_datetime(df["ordered_at"], errors="coerce")
df["order_year"] = ordered_datetime.dt.year.astype("Int64")
df["order_month"] = ordered_datetime.dt.month.astype("Int64")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)