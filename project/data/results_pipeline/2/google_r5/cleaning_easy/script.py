import os
import pandas as pd

input_file = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/customers_raw.csv"
output_file = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r5/cleaning_easy/output.parquet"

df = pd.read_csv(input_file)

for col in df.columns:
    if pd.api.types.is_string_dtype(df[col]) or df[col].dtype == "object":
        df[col] = df[col].str.strip()

df["country"] = df["country"].fillna("UNKNOWN")

os.makedirs(os.path.dirname(output_file), exist_ok=True)
df.to_parquet(output_file, index=False)