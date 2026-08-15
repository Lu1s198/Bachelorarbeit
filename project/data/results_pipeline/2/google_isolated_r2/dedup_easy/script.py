import os
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_hard/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_isolated_r2/dedup_easy/output.parquet"

os.makedirs(os.path.dirname(output_path), exist_ok=True)

df = pd.read_parquet(input_path)
df_dedup = df.drop_duplicates(keep="first")
df_dedup.to_parquet(output_path, index=False)