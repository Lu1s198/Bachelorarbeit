import os
import datetime
import pandas as pd
import numpy as np

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/cleaning_easy/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)

def normalize_date(val):
    if pd.isna(val) or val is None:
        return np.nan
    if isinstance(val, (pd.Timestamp, datetime.date, datetime.datetime)):
        return val.strftime('%Y-%m-%d')
    val_str = str(val).strip()
    if not val_str:
        return np.nan
    
    try:
        num = float(val_str)
        if 1e8 <= num <= 4e9:
            return pd.to_datetime(num, unit='s').strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        pass

    if '.' in val_str:
        try:
            return pd.to_datetime(val_str, dayfirst=True).strftime('%Y-%m-%d')
        except Exception:
            pass

    try:
        return pd.to_datetime(val_str, format='mixed').strftime('%Y-%m-%d')
    except Exception:
        pass

    try:
        return pd.to_datetime(val_str).strftime('%Y-%m-%d')
    except Exception:
        return np.nan

df['registered_at'] = df['registered_at'].apply(normalize_date)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)