import pandas as pd
import numpy as np

# Load data from Parquet file
df = pd.read_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama/cleaning_medium/output.parquet')

# Define a function to map country names to ISO-3166-1-alpha-2 codes
def get_iso_code(country):
    iso_codes = {
        'Germany': 'DE',
        'United States': 'US',
        # Add more mappings as needed
    }
    return iso_codes.get(country, 'UNKNOWN')

# Apply the function to the country column
df['country'] = df['country'].apply(get_iso_code)

# Write the resulting table to a new Parquet file
df.to_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama/cleaning_hard/output.parquet', index=False)