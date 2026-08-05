import pandas as pd
import numpy as np
import os

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/customers_raw.csv"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/cleaning_easy/output.parquet"

df = pd.read_csv(input_path, dtype=str)

for col in df.columns:
    if df[col].dtype == object:
        df[col] = df[col].str.strip()

df['country'] = df['country'].replace('', np.nan)
df['country'] = df['country'].fillna('UNKNOWN')

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)