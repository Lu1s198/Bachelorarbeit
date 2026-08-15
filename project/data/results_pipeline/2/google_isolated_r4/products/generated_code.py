import os
import re
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_isolated_r4/products/output.parquet"

df = pd.read_csv(input_path)

def parse_price(val):
    if pd.isna(val):
        return None
    val_str = str(val).replace('€', '').replace('EUR', '').strip()
    m = re.search(r'[\d.,]+', val_str)
    if not m:
        return None
    s = m.group(0)
    if '.' in s and ',' in s:
        if s.find('.') < s.find(','):
            s = s.replace('.', '').replace(',', '.')
        else:
            s = s.replace(',', '')
    elif ',' in s:
        s = s.replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return None

def parse_bool(val):
    if pd.isna(val):
        return None
    s = str(val).strip().lower()
    if s in ['ja', 'true', '1', 'yes', 't', 'j', 'y']:
        return True
    if s in ['nein', 'false', '0', 'no', 'f', 'n']:
        return False
    return None

df['price_eur'] = df['price_eur'].apply(parse_price).astype(float)
df['in_stock'] = df['in_stock'].apply(parse_bool).astype('boolean')

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)