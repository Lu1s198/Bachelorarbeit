import os
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/customers_raw.csv"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google_isolated/cleaning_easy/output.parquet"

os.makedirs(os.path.dirname(output_path), exist_ok=True)

df = pd.read_csv(input_path)

df["country"] = df["country"].fillna("UNKNOWN")

text_columns = ["full_name", "email", "country", "registered_at"]
for col in text_columns:
    if col in df.columns:
        df[col] = df[col].str.strip()

df.to_parquet(output_path, index=False)