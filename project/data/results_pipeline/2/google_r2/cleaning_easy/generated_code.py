import os
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/customers_raw.csv"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r2/cleaning_easy/output.parquet"

df = pd.read_csv(input_path)

for col in df.columns:
    if pd.api.types.is_string_dtype(df[col]) or df[col].dtype == "object":
        df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

df["country"] = df["country"].fillna("UNKNOWN")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)