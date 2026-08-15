import os
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/customers_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r5/cleaning_easy/output.parquet"

df = pd.read_csv(input_path)

for column in df.columns:
    if pd.api.types.is_string_dtype(df[column]) or df[column].dtype == object:
        df[column] = df[column].astype("string").str.strip()

df["country"] = df["country"].fillna("UNKNOWN")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)