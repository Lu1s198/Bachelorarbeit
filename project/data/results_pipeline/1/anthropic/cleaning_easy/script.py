import pandas as pd
import numpy as np

df = pd.read_csv("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/customers_raw.csv", dtype={"customer_id": "int64"})

for col in ["full_name", "email", "country", "registered_at"]:
    df[col] = df[col].astype(str).str.strip()
    df[col] = df[col].replace({"nan": np.nan, "None": np.nan})

df["country"] = df["country"].fillna("UNKNOWN")

df.to_parquet("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/cleaning_easy/output.parquet", index=False)