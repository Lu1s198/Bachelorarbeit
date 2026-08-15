import os
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r4/dedup_easy/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r4/dedup_medium/output.parquet"

df = pd.read_parquet(input_path)

df = df.sort_values(by="registered_at", ascending=True)
df = df.drop_duplicates(subset=["email"], keep="last")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)