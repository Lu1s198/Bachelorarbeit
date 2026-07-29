import pandas as pd
import numpy as np
import os

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/customers_raw.csv"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/cleaning_easy/output.parquet"

df = pd.read_csv(input_path)

for col in df.select_dtypes(include=['object']).columns:
    df[col] = df[col].str.strip()

if 'country' in df.columns:
    df['country'] = df['country'].replace('', np.nan)
    df['country'] = df['country'].fillna('UNKNOWN')

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)