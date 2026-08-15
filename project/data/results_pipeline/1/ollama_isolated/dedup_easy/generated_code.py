import pandas as pd
import numpy as np

# Read input data
input_file = 'C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/_reference/cleaning_hard/output.parquet'
df = pd.read_parquet(input_file)

# Drop exact duplicates, keeping the first occurrence
df_dedup = df.drop_duplicates(subset=['customer_id', 'full_name', 'email', 'country', 'registered_at'], keep='first')

# Write result to Parquet file
output_file = 'C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama_isolated/dedup_easy/output.parquet'
df_dedup.to_parquet(output_file, index=False)