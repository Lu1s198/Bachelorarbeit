import pandas as pd

df = pd.read_parquet("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/dedup_easy/output.parquet")

df['registered_at_dt'] = pd.to_datetime(df['registered_at'], format='%Y-%m-%d')
df = df.sort_values('registered_at_dt', ascending=False)
df = df.drop_duplicates(subset='email', keep='first')
df = df.drop(columns=['registered_at_dt'])

df.to_parquet("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_isolated_r2/dedup_medium/output.parquet", index=False)