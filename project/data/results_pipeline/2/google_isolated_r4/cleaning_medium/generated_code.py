import os
import pandas as pd

input_file = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_easy/output.parquet"
output_file = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_isolated_r4/cleaning_medium/output.parquet"

df = pd.read_parquet(input_file)

def normalize_date(val):
    if pd.isna(val) or val is None:
        return None
    s = str(val).strip()
    if not s:
        return None

    try:
        num = float(s)
        if 100000000 <= num <= 4102444800:
            return pd.to_datetime(num, unit='s', utc=True).strftime('%Y-%m-%d')
    except ValueError:
        pass

    if '.' in s:
        try:
            dt = pd.to_datetime(s, dayfirst=True, errors='coerce')
            if pd.notna(dt):
                return dt.strftime('%Y-%m-%d')
        except Exception:
            pass

    try:
        dt = pd.to_datetime(s, format='mixed', errors='coerce')
        if pd.notna(dt):
            return dt.strftime('%Y-%m-%d')
    except Exception:
        pass

    try:
        dt = pd.to_datetime(s, errors='coerce')
        if pd.notna(dt):
            return dt.strftime('%Y-%m-%d')
    except Exception:
        pass

    return s

df['registered_at'] = df['registered_at'].apply(normalize_date)

os.makedirs(os.path.dirname(output_file), exist_ok=True)
df.to_parquet(output_file, index=False)