import pandas as pd
import numpy as np

df = pd.read_csv(
    "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/customers_raw.csv",
    dtype={"customer_id": "int64"}
)

for col in ["full_name", "email", "country", "registered_at"]:
    df[col] = df[col].astype(str).str.strip()
    df[col] = df[col].where(~df[col].isin(["nan", "None", "NaN", "<NA>"]), np.nan)

df["country"] = df["country"].fillna("UNKNOWN")

df.to_parquet(
    "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_isolated_r3/cleaning_easy/output.parquet",
    index=False
)