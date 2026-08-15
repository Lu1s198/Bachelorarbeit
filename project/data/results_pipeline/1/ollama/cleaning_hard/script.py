import pandas as pd
import numpy as np

# Load data from Parquet file
df = pd.read_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama/cleaning_medium/output.parquet')

# Define a function to map country codes
def map_country(country):
    iso_codes = {
        'Deutschland': 'DE',
        'Germany': 'DE',
        'USA': 'US',
        # Add more mappings as needed
    }
    
    if country in iso_codes:
        return iso_codes[country]
    elif len(country) == 2 and country.isalpha():
        return country.upper()
    else:
        return 'UNKNOWN'

# Apply the mapping function to the 'country' column
df['country'] = df['country'].apply(map_country)

# Ensure key columns are of the same type (int64)
df['customer_id'] = df['customer_id'].astype(np.int64)

# Write the resulting table as a Parquet file
df.to_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama/cleaning_hard/output.parquet', index=False)