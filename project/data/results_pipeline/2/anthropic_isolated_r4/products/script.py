import pandas as pd
import numpy as np
import re
import os

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_isolated_r4/products/output.parquet"

df = pd.read_csv(input_path, dtype={"product_id": "int64"})

def parse_price(val):
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    s = re.sub(r'[^0-9,.\-]', '', s)
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

def parse_bool(val):
    if pd.isna(val):
        return None
    s = str(val).strip().lower()
    true_vals = {'ja', 'true', '1', 'yes', 'y', 'wahr'}
    false_vals = {'nein', 'false', '0', 'no', 'n', 'falsch'}
    if s in true_vals:
        return True
    if s in false_vals:
        return False
    return None

df['price_eur'] = df['price_eur'].apply(parse_price).astype(float)
df['in_stock'] = df['in_stock'].apply(parse_bool).astype('boolean')

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)