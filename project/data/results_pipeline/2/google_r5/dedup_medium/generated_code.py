import os
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r5/dedup_easy/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r5/dedup_medium/output.parquet"

df = pd.read_parquet(input_path)

df['_temp_reg'] = pd.to_datetime(df['registered_at'])
df = df.sort_values('_temp_reg', ascending=True)
df = df.drop_duplicates(subset=['email'], keep='last')
df = df.drop(columns=['_temp_reg'])

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)