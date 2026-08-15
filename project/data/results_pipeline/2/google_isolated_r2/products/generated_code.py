import os
import re
import pandas as pd

input_file = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv"
output_file = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_isolated_r2/products/output.parquet"

df = pd.read_csv(input_file)

def clean_price(val):
    if pd.isna(val):
        return None
    val = str(val).strip()
    val = re.sub(r'[^\d.,-]', '', val)
    if not val:
        return None
    if '.' in val and ',' in val:
        if val.rfind('.') < val.rfind(','):
            val = val.replace('.', '').replace(',', '.')
        else:
            val = val.replace(',', '')
    elif ',' in val:
        val = val.replace(',', '.')
    try:
        return float(val)
    except ValueError:
        return None

def clean_bool(val):
    if pd.isna(val):
        return None
    s = str(val).strip().lower()
    if s in {'ja', 'true', '1', 'yes', 'y', 't', 'wahr', '1.0'}:
        return True
    if s in {'nein', 'false', '0', 'no', 'n', 'f', 'falsch', '0.0'}:
        return False
    return None

df['product_id'] = df['product_id'].astype('int64')
df['price_eur'] = df['price_eur'].apply(clean_price)
df['in_stock'] = df['in_stock'].apply(clean_bool)

os.makedirs(os.path.dirname(output_file), exist_ok=True)
df.to_parquet(output_file, index=False)