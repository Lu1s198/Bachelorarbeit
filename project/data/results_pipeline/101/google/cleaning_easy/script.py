import os
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/101/customers_raw.csv"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/google/cleaning_easy/output.parquet"

df = pd.read_csv(input_path)

for col in df.select_dtypes(include=["object", "string"]).columns:
    df[col] = df[col].str.strip()

df["country"] = df["country"].fillna("UNKNOWN")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)