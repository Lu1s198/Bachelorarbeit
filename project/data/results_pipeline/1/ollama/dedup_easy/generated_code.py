import pandas as pd
import numpy as np

# Load data from Parquet file
df = pd.read_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama/cleaning_hard/output.parquet')

# Drop exact duplicates, keeping the first occurrence
df_dedup = df.drop_duplicates(subset=None, keep='first', inplace=False)

# Select required columns
df_dedup = df_dedup[['customer_id', 'full_name', 'email', 'country', 'registered_at']]

# Write result to Parquet file
df_dedup.to_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama/dedup_easy/output.parquet')