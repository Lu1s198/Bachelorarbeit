import pandas as pd
import numpy as np

# Load data from CSV file
df = pd.read_csv('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/products_raw.csv')

# Define a function to convert price_eur column to float
def convert_price_eur(x):
    x = str(x).replace('€', '').replace('EUR', '')
    if ',' in x:
        return np.float64(x.replace('.', '').replace(',', '.'))
    else:
        return np.float64(x)

# Apply the function to the price_eur column
df['price_eur'] = df['price_eur'].apply(convert_price_eur)

# Define a function to convert in_stock column to boolean
def convert_in_stock(x):
    if x.lower() == 'ja' or x.lower() == 'true' or x == '1':
        return True
    else:
        return False

# Apply the function to the in_stock column
df['in_stock'] = df['in_stock'].apply(convert_in_stock)

# Select required columns
df = df[['product_id', 'name', 'category', 'price_eur', 'in_stock']]

# Write the resulting table as a Parquet file
df.to_parquet('C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/ollama/products/output.parquet')