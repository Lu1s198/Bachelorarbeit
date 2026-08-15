import pandas as pd

df = pd.read_csv("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/101/customers_raw.csv")

for col in df.columns:
    if df[col].dtype == object:
        df[col] = df[col].str.strip()

df["country"] = df["country"].fillna("UNKNOWN")
mask = df["country"].isna() | (df["country"].astype(str).str.lower() == "nan")
df.loc[mask, "country"] = "UNKNOWN"

df.to_parquet(
    "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/anthropic_isolated/cleaning_easy/output.parquet",
    index=False
)