import pandas as pd
import numpy as np

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r2/cleaning_easy/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r2/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)

def normalize_date(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s == "":
        return None
    if s.isdigit():
        try:
            ts = int(s)
            dt = pd.to_datetime(ts, unit='s')
            return dt.strftime('%Y-%m-%d')
        except Exception:
            pass
    for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%B %d %Y', '%b %d %Y'):
        try:
            dt = pd.to_datetime(s, format=fmt)
            return dt.strftime('%Y-%m-%d')
        except Exception:
            continue
    try:
        dt = pd.to_datetime(s)
        return dt.strftime('%Y-%m-%d')
    except Exception:
        return None

df['registered_at'] = df['registered_at'].apply(normalize_date)

df.to_parquet(output_path, index=False)