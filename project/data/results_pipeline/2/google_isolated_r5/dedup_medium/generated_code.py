import os
import pandas as pd

input_file = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_easy/output.parquet"
output_file = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_isolated_r5/dedup_medium/output.parquet"

df = pd.read_parquet(input_file)
df = df.sort_values(by="registered_at", ascending=False)
df = df.drop_duplicates(subset=["email"], keep="first")

os.makedirs(os.path.dirname(output_file), exist_ok=True)
df.to_parquet(output_file, index=False)