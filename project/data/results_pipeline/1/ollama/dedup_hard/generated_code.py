import pandas as pd
from numpy import unique

# Load data from Parquet file
df = pd.read_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama/dedup_medium/output.parquet')

# Function to normalize name and email
def normalize_name(name):
    return ' '.join([x.strip() for x in name.split()])
    
def normalize_email(email):
    if '.' in email:
        email = email.replace('.', '')
    return email.lower()

# Apply function to full_name and email columns
df['full_name'] = df.apply(lambda row: normalize_name(row['full_name']), axis=1)
df['email'] = df.apply(lambda row: normalize_email(row['email']), axis=1)

# Group by normalized name, email, country and registered_at, take the first occurrence of each group
df_dedup = df.groupby(['full_name', 'email', 'country', 'registered_at']).first().reset_index()

# Write result to Parquet file
df_dedup.to_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama/dedup_hard/output.parquet')