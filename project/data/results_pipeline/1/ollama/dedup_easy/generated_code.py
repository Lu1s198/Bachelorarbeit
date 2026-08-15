import pandas as pd
import numpy as np

# Read input data
df = pd.read_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama/cleaning_hard/output.parquet')

# Drop exact duplicates, keeping the first occurrence
df_dedup = df.drop_duplicates(subset=None, keep='first', inplace=False)

# Write result to Parquet file
df_dedup.to_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama/dedup_easy/output.parquet')