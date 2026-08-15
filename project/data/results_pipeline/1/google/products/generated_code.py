import os
import re
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/products_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/products/output.parquet"

df = pd.read_csv(input_path)

def clean_price(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    s = re.sub(r'[^0-9.,]', '', s)
    if not s:
        return None
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
        return None

def clean_bool(val):
    if pd.isna(val):
        return None
    s = str(val).strip().lower()
    if s in {'ja', 'true', '1', 'yes', 't', 'y', '1.0'}:
        return True
    if s in {'nein', 'false', '0', 'no', 'f', 'n', '0.0'}:
        return False
    return None

df['price_eur'] = df['price_eur'].apply(clean_price)
df['in_stock'] = df['in_stock'].apply(clean_bool).astype('boolean')

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)