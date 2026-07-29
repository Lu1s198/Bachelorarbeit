import pandas as pd
import numpy as np

# Load data from CSV file
df = pd.read_csv('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/customers_raw.csv')

# Remove leading and trailing whitespaces from text columns
text_cols = ['full_name', 'email']
for col in text_cols:
    df[col] = df[col].str.strip()

# Replace missing values in 'country' column with 'UNKNOWN'
df['country'] = df['country'].fillna('UNKNOWN')

# Ensure key columns are of the same type to avoid type mismatch errors
df['customer_id'] = pd.to_numeric(df['customer_id'], downcast='integer')
df['registered_at'] = pd.to_datetime(df['registered_at'])

# Write resulting table as a Parquet file
df.to_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama/cleaning_easy/output.parquet', index=False)