import pandas as pd
from numpy import unique

# Read input data
df = pd.read_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/_reference/dedup_medium/output.parquet')

# Function to normalize name and email
def normalize_name_and_email(row):
    # Remove title and honorifics from full_name
    name = row['full_name'].split()[0]
    
    # Normalize name (lowercase, remove punctuation)
    normalized_name = ''.join(e for e in name if e.isalnum() or e.isspace()).strip().lower()
    
    # Normalize email (remove dots before @)
    normalized_email = row['email'].replace('.', '')
    
    return pd.Series([normalized_name, normalized_email])

# Apply function to each row
df[['normalized_name', 'normalized_email']] = df.apply(normalize_name_and_email, axis=1, result_type='expand')

# Group by normalized name and email, keep the smallest customer_id for duplicates
df_grouped = df.groupby(['normalized_name', 'normalized_email']).agg({'customer_id': 'min', 
                                                                        'full_name': 'first',
                                                                        'email': 'first',
                                                                        'country': 'first',
                                                                        'registered_at': 'first'})

# Reset index to get original column names back
df_grouped.reset_index(inplace=True)

# Write result as Parquet file
df_grouped.to_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama_isolated/dedup_hard/output.parquet', index=False)