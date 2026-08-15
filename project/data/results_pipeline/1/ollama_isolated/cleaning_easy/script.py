import pandas as pd
from numpy import nan

# Read the input CSV file
df = pd.read_csv('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/customers_raw.csv')

# Remove leading and trailing whitespaces from text columns
df['full_name'] = df['full_name'].str.strip()
df['email'] = df['email'].str.strip()

# Replace missing values in the 'country' column with 'UNKNOWN'
df['country'] = df['country'].fillna('UNKNOWN').astype(str)

# Write the resulting table to a Parquet file
df.to_parquet(
    'C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama_isolated/cleaning_easy/output.parquet',
    index=False,
    engine='pyarrow'
)