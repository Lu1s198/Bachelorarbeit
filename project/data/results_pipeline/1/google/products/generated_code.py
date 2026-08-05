import os
import re
import pandas as pd
import numpy as np

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/products_raw.csv"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/products/output.parquet"

df = pd.read_csv(input_path)

def clean_price(val):
    if pd.isna(val):
        return np.nan
    s = str(val)
    s = re.sub(r'[^0-9.,-]', '', s)
    if not s:
        return np.nan
    if ',' in s and '.' in s:
        if s.rfind(',') > s.rfind('.'):
            s = s.replace('.', '').replace(',', '.')
        else:
            s = s.replace(',', '')
    elif ',' in s:
        s = s.replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return np.nan

if 'price_eur' in df.columns:
    df['price_eur'] = df['price_eur'].apply(clean_price)

if 'in_stock' in df.columns:
    true_set = {'ja', 'true', '1', 'yes', '1.0', 't', 'y'}
    df['in_stock'] = df['in_stock'].astype(str).str.strip().str.lower().isin(true_set)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)