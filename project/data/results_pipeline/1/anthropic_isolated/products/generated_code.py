import pandas as pd
import numpy as np
import re
import os

df = pd.read_csv("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/products_raw.csv")

def parse_price(val):
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    s = s.replace('€', '').replace('EUR', '').replace('eur', '')
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
    if s == '' or s == '-':
        return np.nan
    try:
        return float(s)
    except ValueError:
        return np.nan

def parse_bool(val):
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

df['price_eur'] = df['price_eur'].apply(parse_price).astype(float)
df['in_stock'] = df['in_stock'].apply(parse_bool).astype('boolean')

out_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic_isolated/products/output.parquet"
os.makedirs(os.path.dirname(out_path), exist_ok=True)
df.to_parquet(out_path, index=False)