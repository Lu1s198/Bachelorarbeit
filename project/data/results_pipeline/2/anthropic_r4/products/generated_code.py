import pandas as pd
import numpy as np
import re
import os

df = pd.read_csv("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv")

def clean_price(val):
    if pd.isna(val):
        return np.nan
    s = str(val)
    s = re.sub(r'[^0-9,.\-]', '', s)
    s = s.strip()
    if ',' in s and '.' in s:
        if s.rfind(',') > s.rfind('.'):
            s = s.replace('.', '')
            s = s.replace(',', '.')
        else:
            s = s.replace(',', '')
    elif ',' in s:
        s = s.replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return np.nan

def clean_bool(val):
    if pd.isna(val):
        return None
    s = str(val).strip().lower()
    true_vals = {'ja', 'true', '1', 'yes', 'wahr'}
    false_vals = {'nein', 'false', '0', 'no', 'falsch'}
    if s in true_vals:
        return True
    elif s in false_vals:
        return False
    else:
        return None

df['price_eur'] = df['price_eur'].apply(clean_price).astype(float)
df['in_stock'] = df['in_stock'].apply(clean_bool).astype('boolean')

df['product_id'] = df['product_id'].astype('int64')
df['name'] = df['name'].astype(str)
df['category'] = df['category'].astype(str)

output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r4/products/output.parquet"
os.makedirs(os.path.dirname(output_path), exist_ok=True)

df.to_parquet(output_path, index=False)