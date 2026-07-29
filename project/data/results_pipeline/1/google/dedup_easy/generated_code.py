import os
import pandas as pd

input_file = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/cleaning_hard/output.parquet"
output_file = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/dedup_easy/output.parquet"

df = pd.read_parquet(input_file)
df_dedup = df.drop_duplicates(keep="first")

os.makedirs(os.path.dirname(output_file), exist_ok=True)
df_dedup.to_parquet(output_file, index=False)