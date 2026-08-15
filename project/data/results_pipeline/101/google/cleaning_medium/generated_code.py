import os
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/google/cleaning_easy/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/google/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)

def parse_date(val):
    if pd.isna(val):
        return val
    s = str(val).strip()
    if not s:
        return s
    
    try:
        num = float(s)
        if 100000000 < num < 4102444800:
            dt = pd.to_datetime(num, unit='s', errors='coerce')
            if pd.notna(dt):
                return dt.strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        pass

    if '.' in s:
        dt = pd.to_datetime(s, format='%d.%m.%Y', errors='coerce')
        if pd.notna(dt):
            return dt.strftime('%Y-%m-%d')

    dt = pd.to_datetime(s, errors='coerce')
    if pd.notna(dt):
        return dt.strftime('%Y-%m-%d')

    return s

df['registered_at'] = df['registered_at'].apply(parse_date)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)