import pandas as pd
import numpy as np

# Load data from Parquet file
df = pd.read_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama/cleaning_easy/output.parquet')

# Function to convert mixed date formats to ISO format
def convert_date(date_str):
    if isinstance(date_str, int):  # Unix timestamp
        return pd.to_datetime(np.datetime64(str(date_str), 's')).strftime('%Y-%m-%d')
    elif '.' in date_str:  # German or US date format
        try:
            return pd.to_datetime(date_str.replace('.', '-', 1)).strftime('%Y-%m-%d')
        except ValueError:
            pass
    return date_str

# Apply the conversion function to the 'registered_at' column
df['registered_at'] = df['registered_at'].apply(convert_date)

# Write the resulting table as a Parquet file
df.to_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama/cleaning_medium/output.parquet', index=False)