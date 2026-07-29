import pandas as pd

df = pd.read_parquet("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/dedup_easy/output.parquet")

df['registered_at'] = df['registered_at'].astype(str)

df = df.sort_values('registered_at', ascending=False).drop_duplicates(subset='email', keep='first')

df.to_parquet("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/dedup_medium/output.parquet", index=False)