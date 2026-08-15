import pandas as pd

df = pd.read_csv("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/customers_raw.csv")

for col in df.select_dtypes(include="object").columns:
    df[col] = df[col].str.strip()

df["country"] = df["country"].fillna("UNKNOWN")
df.loc[df["country"] == "", "country"] = "UNKNOWN"

df.to_parquet(
    "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_isolated_r2/cleaning_easy/output.parquet",
    index=False
)