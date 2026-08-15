import pandas as pd
import numpy as np

# Read the input CSV file
df = pd.read_csv('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/products_raw.csv')

# Define a function to convert price_eur column
def convert_price_eur(x):
    x = x.replace('€', '').replace('EUR', '')
    if ',' in x:
        return float(x.replace('.', '').replace(',', '.'))
    else:
        return float(x)

# Apply the conversion function to the price_eur column
df['price_eur'] = df['price_eur'].apply(convert_price_eur)

# Define a function to convert in_stock column
def convert_in_stock(x):
    if x.lower() == 'ja' or x.lower() == 'true' or x == '1':
        return True
    elif x.lower() == 'nein' or x.lower() == 'false' or x == '0':
        return False

# Apply the conversion function to the in_stock column
df['in_stock'] = df['in_stock'].apply(convert_in_stock)

# Write the resulting table as a Parquet file
df.to_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama/products/output.parquet', index=False)