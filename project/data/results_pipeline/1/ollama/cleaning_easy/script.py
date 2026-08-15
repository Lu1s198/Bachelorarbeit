import pandas as pd
from numpy import nan
import os

# Read the input CSV file
input_file = 'C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/customers_raw.csv'
df = pd.read_csv(input_file)

# Remove leading and trailing whitespaces from text columns
for col in ['full_name', 'email']:
    df[col] = df[col].str.strip()

# Replace missing values in the country column with 'UNKNOWN'
df['country'] = df['country'].fillna('UNKNOWN')

# Ensure key columns are of the same type to avoid type mismatch errors
df['customer_id'] = pd.to_numeric(df['customer_id'], downcast='integer')
df['registered_at'] = pd.to_datetime(df['registered_at'])

# Write the resulting table as a Parquet file
output_file = 'C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama/cleaning_easy/output.parquet'
os.makedirs(os.path.dirname(output_file), exist_ok=True)
df.to_parquet(output_file, index=False)