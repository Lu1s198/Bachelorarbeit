import pandas as pd

df = pd.read_csv("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/customers_raw.csv")

str_cols = df.select_dtypes(include="object").columns
for col in str_cols:
    df[col] = df[col].str.strip()

df["country"] = df["country"].fillna("UNKNOWN")
df["country"] = df["country"].replace("", "UNKNOWN")

df.to_parquet("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r2/cleaning_easy/output.parquet", index=False)