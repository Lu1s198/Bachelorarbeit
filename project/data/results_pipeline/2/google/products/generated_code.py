import os
import re
import pandas as pd
import numpy as np

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google/products/output.parquet"

df = pd.read_csv(input_path)

def parse_price(val):
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    s = re.sub(r'[^0-9.,]', '', s)
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

def parse_bool(val):
    if pd.isna(val):
        return pd.NA
    s = str(val).strip().lower()
    if s in ['ja', 'true', '1', 'yes', 'y', 't', 'wahr']:
        return True
    elif s in ['nein', 'false', '0', 'no', 'n', 'f', 'falsch']:
        return False
    return pd.NA

df['price_eur'] = df['price_eur'].apply(parse_price)
df['in_stock'] = df['in_stock'].apply(parse_bool).astype('boolean')

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)