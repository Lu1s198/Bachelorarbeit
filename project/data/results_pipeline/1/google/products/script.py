import os
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/products_raw.csv"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/products/output.parquet"

def clean_price(val):
    if pd.isna(val):
        return None
    val = str(val).strip()
    if not val:
        return None
    val = val.replace('€', '').replace('EUR', '').replace('eur', '').replace('$', '').strip()
    if ',' in val and '.' in val:
        if val.rfind(',') > val.rfind('.'):
            val = val.replace('.', '').replace(',', '.')
        else:
            val = val.replace(',', '')
    elif ',' in val:
        val = val.replace(',', '.')
    try:
        return float(val)
    except ValueError:
        return None

def clean_in_stock(val):
    if pd.isna(val):
        return None
    s = str(val).strip().lower()
    if s in ['ja', 'true', '1', 'yes', 'j', 't', 'wahr']:
        return True
    elif s in ['nein', 'false', '0', 'no', 'n', 'f', 'falsch']:
        return False
    return None

df = pd.read_csv(input_path)

if 'price_eur' in df.columns:
    df['price_eur'] = df['price_eur'].apply(clean_price)

if 'in_stock' in df.columns:
    df['in_stock'] = df['in_stock'].apply(clean_in_stock).astype('boolean')

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)