import pandas as pd
import numpy as np
import os

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/customers_raw.csv"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r4/cleaning_easy/output.parquet"

df = pd.read_csv(input_path, dtype={"customer_id": "int64"})

for col in df.select_dtypes(include=["object"]).columns:
    df[col] = df[col].str.strip()

df["country"] = df["country"].replace("", np.nan)
df["country"] = df["country"].where(df["country"].notna(), "UNKNOWN")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)