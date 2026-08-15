import os
import pandas as pd

input_file = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/customers_raw.csv"
output_file = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_isolated_r2/cleaning_easy/output.parquet"

df = pd.read_csv(input_file)

text_cols = ["full_name", "email", "country", "registered_at"]

for col in text_cols:
    if col in df.columns:
        df[col] = df[col].astype("string").str.strip()

df["country"] = df["country"].fillna("UNKNOWN")

os.makedirs(os.path.dirname(output_file), exist_ok=True)
df.to_parquet(output_file, index=False)