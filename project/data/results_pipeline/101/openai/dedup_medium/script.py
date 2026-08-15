import os
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/openai/dedup_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/openai/dedup_medium/output.parquet"

df = pd.read_parquet(input_path)

df["_registered_at_sort"] = pd.to_datetime(df["registered_at"], format="%Y-%m-%d", errors="coerce")
df = df.sort_values(
    by="_registered_at_sort",
    ascending=False,
    na_position="last",
    kind="stable"
)
df = df.drop_duplicates(subset=["email"], keep="first")
df = df.drop(columns=["_registered_at_sort"])

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)