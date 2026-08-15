import pandas as pd

df = pd.read_parquet("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_easy/output.parquet")

df['registered_at'] = df['registered_at'].astype(str)
df = df.sort_values('registered_at', ascending=False)
df = df.drop_duplicates(subset='email', keep='first')

df.to_parquet("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_isolated_r3/dedup_medium/output.parquet", index=False)