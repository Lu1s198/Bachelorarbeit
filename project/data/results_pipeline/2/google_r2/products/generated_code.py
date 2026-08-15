import os
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r2/products/output.parquet"

df = pd.read_csv(input_path)

def parse_price(val):
    if pd.isna(val):
        return None
    val_str = str(val).replace('€', '').replace('EUR', '').replace('eur', '').strip()
    if not val_str:
        return None
    if ',' in val_str and '.' in val_str:
        if val_str.find(',') < val_str.find('.'):
            val_str = val_str.replace(',', '')
        else:
            val_str = val_str.replace('.', '').replace(',', '.')
    elif ',' in val_str:
        val_str = val_str.replace(',', '.')
    try:
        return float(val_str)
    except ValueError:
        return None

def parse_bool(val):
    if pd.isna(val):
        return None
    v = str(val).strip().lower()
    if v in ['ja', 'true', '1', 'yes', 'wahr', 'j', 't']:
        return True
    elif v in ['nein', 'false', '0', 'no', 'falsch', 'n', 'f']:
        return False
    return None

df['price_eur'] = df['price_eur'].apply(parse_price).astype(float)
df['in_stock'] = df['in_stock'].apply(parse_bool).astype('boolean')

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)