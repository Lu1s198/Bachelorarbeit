import pandas as pd
import numpy as np
import os

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/customers_raw.csv"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_isolated_r5/cleaning_easy/output.parquet"

df = pd.read_csv(input_path, dtype={"customer_id": "int64"})

text_cols = df.select_dtypes(include="object").columns

for col in text_cols:
    df[col] = df[col].str.strip()

df["country"] = df["country"].replace({"": np.nan})
df["country"] = df["country"].where(df["country"].notna(), "UNKNOWN")
df["country"] = df["country"].fillna("UNKNOWN")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)