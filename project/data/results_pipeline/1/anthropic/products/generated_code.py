import pandas as pd
import numpy as np
import re
import os

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/products_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/products/output.parquet"

df = pd.read_csv(input_path, dtype={'product_id': 'int64'})

def clean_price(val):
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    s = re.sub(r'[€$£]', '', s)
    s = re.sub(r'(?i)\s*eur\s*', '', s)
    s = s.strip()
    if ',' in s and '.' in s:
        if s.rfind(',') > s.rfind('.'):
            s = s.replace('.', '')
            s = s.replace(',', '.')
        else:
            s = s.replace(',', '')
    elif ',' in s:
        s = s.replace(',', '.')
    s = re.sub(r'[^0-9.\-]', '', s)
    try:
        return float(s)
    except ValueError:
        return np.nan

def clean_bool(val):
    if pd.isna(val):
        return np.nan
    s = str(val).strip().lower()
    true_vals = {'ja', 'true', '1', 'yes', 'y', 'wahr'}
    false_vals = {'nein', 'false', '0', 'no', 'n', 'falsch'}
    if s in true_vals:
        return True
    elif s in false_vals:
        return False
    else:
        return np.nan

df['price_eur'] = df['price_eur'].apply(clean_price).astype(float)
df['in_stock'] = df['in_stock'].apply(clean_bool).astype('boolean')

df['product_id'] = df['product_id'].astype('int64')
df['name'] = df['name'].astype(str)
df['category'] = df['category'].astype(str)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)