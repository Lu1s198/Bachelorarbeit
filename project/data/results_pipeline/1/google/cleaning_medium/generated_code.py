import os
import re
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/cleaning_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)

def normalize_date(val):
    if pd.isna(val) or val is None:
        return None
    if isinstance(val, (int, float, np.number)):
        if np.isnan(val):
            return None
        try:
            return pd.to_datetime(val, unit='s').strftime('%Y-%m-%d')
        except Exception:
            return None
    val_str = str(val).strip()
    if not val_str:
        return None
    if re.match(r'^\d+(\.\d+)?$', val_str):
        try:
            num = float(val_str)
            if num > 1e7:
                return pd.to_datetime(num, unit='s').strftime('%Y-%m-%d')
        except Exception:
            pass
    if re.match(r'^\d{1,2}\.\d{1,2}\.\d{4}', val_str):
        try:
            return pd.to_datetime(val_str, format='%d.%m.%Y').strftime('%Y-%m-%d')
        except Exception:
            pass
    try:
        return pd.to_datetime(val_str).strftime('%Y-%m-%d')
    except Exception:
        return None

df['registered_at'] = df['registered_at'].apply(normalize_date)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)