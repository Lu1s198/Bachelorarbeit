import os
import pandas as pd

input_file = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r5/cleaning_hard/output.parquet"
output_file = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r5/dedup_easy/output.parquet"

df = pd.read_parquet(input_file)
df = df.drop_duplicates(keep="first")

os.makedirs(os.path.dirname(output_file), exist_ok=True)
df.to_parquet(output_file, index=False)