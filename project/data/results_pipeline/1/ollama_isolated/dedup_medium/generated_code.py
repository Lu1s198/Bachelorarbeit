import pandas as pd
import numpy as np

# Read input data
input_file = 'C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/_reference/dedup_easy/output.parquet'
df = pd.read_parquet(input_file)

# Ensure email column is of string type to avoid potential errors
df['email'] = df['email'].astype(str)

# Remove duplicate rows based on email and keep the row with the latest registered_at value
df = df.loc[df.groupby('email')['registered_at'].idxmax()]

# Write result as Parquet file
output_file = 'C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama_isolated/dedup_medium/output.parquet'
df.to_parquet(output_file, index=False)