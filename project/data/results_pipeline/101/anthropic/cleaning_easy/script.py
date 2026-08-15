import pandas as pd
import numpy as np

df = pd.read_csv(
    "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/101/customers_raw.csv",
    dtype={"customer_id": "int64"}
)

for col in df.select_dtypes(include=["object"]).columns:
    df[col] = df[col].str.strip()

df["country"] = df["country"].replace(r"^\s*$", np.nan, regex=True)
df["country"] = df["country"].where(df["country"].notna(), "UNKNOWN")
df["country"] = df["country"].fillna("UNKNOWN")

df.to_parquet(
    "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/anthropic/cleaning_easy/output.parquet",
    index=False
)