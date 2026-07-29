import pandas as pd
from datetime import datetime

# Load data from Parquet file
df = pd.read_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama/dedup_easy/output.parquet')

# Remove duplicate rows based on 'email' column and keep the row with the latest 'registered_at' value
df = df.loc[df.groupby('email')['registered_at'].idxmax()]

# Select required columns
df = df[['customer_id', 'full_name', 'email', 'country', 'registered_at']]

# Write transformed data to Parquet file
df.to_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama/dedup_medium/output.parquet', index=False)