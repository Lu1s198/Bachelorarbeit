import os
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/google/dedup_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/google/dedup_medium/output.parquet"

df = pd.read_parquet(input_path)

df_sorted = df.sort_values(by="registered_at", ascending=False)
df_dedup = df_sorted.drop_duplicates(subset=["email"], keep="first")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df_dedup.to_parquet(output_path, index=False)