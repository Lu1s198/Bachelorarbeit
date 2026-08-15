import os
import pandas as pd
import numpy as np

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r5/cleaning_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r5/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)

def parse_registered_at(val):
    if pd.isna(val) or val is None:
        return np.nan
    val_str = str(val).strip()
    if not val_str or val_str.lower() in ('nan', 'none', 'null'):
        return np.nan
    
    try:
        clean_num_str = val_str[:-2] if val_str.endswith('.0') else val_str
        if clean_num_str.isdigit():
            num = int(clean_num_str)
            if num > 100000000:
                return pd.to_datetime(num, unit='s').strftime('%Y-%m-%d')
    except Exception:
        pass

    if '.' in val_str:
        try:
            return pd.to_datetime(val_str, format='%d.%m.%Y').strftime('%Y-%m-%d')
        except Exception:
            try:
                return pd.to_datetime(val_str, dayfirst=True).strftime('%Y-%m-%d')
            except Exception:
                pass

    try:
        return pd.to_datetime(val_str, format='mixed').strftime('%Y-%m-%d')
    except Exception:
        try:
            return pd.to_datetime(val_str).strftime('%Y-%m-%d')
        except Exception:
            return np.nan

df['registered_at'] = df['registered_at'].apply(parse_registered_at)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)