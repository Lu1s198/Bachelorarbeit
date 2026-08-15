import pandas as pd
import numpy as np

# Load data from Parquet file
df = pd.read_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/_reference/cleaning_easy/output.parquet')

# Define a function to normalize the 'registered_at' column
def normalize_registered_at(x):
    if isinstance(x, str):
        try:
            return pd.to_datetime(x, format='%m.%d.%Y').strftime('%Y-%m-%d')
        except ValueError:
            try:
                return pd.to_datetime(x, format='Month DD YYYY').strftime('%Y-%m-%d')
            except ValueError:
                try:
                    return pd.to_datetime(x, format='%Y-%m-%d').strftime('%Y-%m-%d')
                except ValueError:
                    try:
                        return pd.to_datetime(x, unit='s').strftime('%Y-%m-%d')
                    except ValueError:
                        return x
    else:
        return np.nan

# Apply the function to the 'registered_at' column
df['registered_at'] = df['registered_at'].apply(normalize_registered_at)

# Write the resulting table as a Parquet file
df.to_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama_isolated/cleaning_medium/output.parquet', index=False)