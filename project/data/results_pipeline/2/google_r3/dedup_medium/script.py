import os
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r3/dedup_easy/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r3/dedup_medium/output.parquet"

df = pd.read_parquet(input_path)

df["registered_at_dt"] = pd.to_datetime(df["registered_at"])
df = df.sort_values(by="registered_at_dt", ascending=True)
df = df.drop_duplicates(subset=["email"], keep="last")
df = df.drop(columns=["registered_at_dt"])

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)