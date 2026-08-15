import os
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/101/products_raw.csv"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/google_isolated/products/output.parquet"

df = pd.read_csv(input_path)

def clean_price(val):
    if pd.isna(val):
        return None
    s = str(val).replace('€', '').replace('EUR', '').strip()
    s = ''.join(c for c in s if c.isdigit() or c in ['.', ','])
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

def clean_in_stock(val):
    if pd.isna(val):
        return False
    s = str(val).strip().lower()
    return s in {'ja', 'true', '1', 'yes', 't', 'j', '1.0'}

df['price_eur'] = df['price_eur'].apply(clean_price)
df['in_stock'] = df['in_stock'].apply(clean_in_stock).astype(bool)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)