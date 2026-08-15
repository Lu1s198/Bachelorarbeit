import pandas as pd

df = pd.read_parquet("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r2/cleaning_hard/output.parquet")
df = df.drop_duplicates(keep="first")
df.to_parquet("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r2/dedup_easy/output.parquet", index=False)