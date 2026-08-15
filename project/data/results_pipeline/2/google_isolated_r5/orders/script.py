import os
import pandas as pd

input_path = (
    "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/orders_raw.csv"
)
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_isolated_r5/orders/output.parquet"

df = pd.read_csv(input_path)

df["total_eur"] = df["quantity"] * df["unit_price_eur"]

dt_series = pd.to_datetime(df["ordered_at"])
df["order_year"] = dt_series.dt.year.astype("int64")
df["order_month"] = dt_series.dt.month.astype("int64")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)