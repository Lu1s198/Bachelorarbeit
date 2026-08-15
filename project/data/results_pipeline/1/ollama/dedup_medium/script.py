import pandas as pd
import numpy as np

# Read input data
df = pd.read_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama/dedup_easy/output.parquet')

# Convert registered_at to datetime for correct sorting
df['registered_at'] = pd.to_datetime(df['registered_at'])

# Group by email and keep the row with the latest registered_at value
df = df.loc[df.groupby('email')['registered_at'].idxmax()]

# Write result as Parquet file
df.to_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama/dedup_medium/output.parquet', index=False)