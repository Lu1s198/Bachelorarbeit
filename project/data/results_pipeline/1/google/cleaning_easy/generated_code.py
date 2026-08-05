import os
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/customers_raw.csv"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/cleaning_easy/output.parquet"

os.makedirs(os.path.dirname(output_path), exist_ok=True)

df = pd.read_csv(input_path)

for col in df.select_dtypes(include=["object", "string"]).columns:
    df[col] = df[col].str.strip()

if "country" in df.columns:
    df["country"] = df["country"].fillna("UNKNOWN").replace("", "UNKNOWN")

df.to_parquet(output_path, index=False)