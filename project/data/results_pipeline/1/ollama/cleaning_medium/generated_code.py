import pandas as pd
import numpy as np

# Load data from Parquet file
df = pd.read_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama/cleaning_easy/output.parquet')

# Function to convert Unix timestamp to ISO date
def unix_to_iso(timestamp):
    return pd.to_datetime(int(timestamp), unit='s').strftime('%Y-%m-%d')

# Apply conversion function to 'registered_at' column
df['registered_at'] = df['registered_at'].apply(lambda x: 
    pd.to_datetime(x, format='%d.%m.%Y', errors='coerce').strftime('%Y-%m-%d') if isinstance(x, str) and '.' in x else 
    pd.to_datetime(x, format='%B %d %Y', errors='coerce').strftime('%Y-%m-%d') if isinstance(x, str) and ' ' in x else 
    unix_to_iso(x) if isinstance(x, int) else 
    x)

# Write result to Parquet file
df.to_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama/cleaning_medium/output.parquet', index=False)