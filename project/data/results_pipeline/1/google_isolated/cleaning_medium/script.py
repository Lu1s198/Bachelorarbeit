import os
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/_reference/cleaning_easy/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google_isolated/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)

def parse_registered_at(val):
    if pd.isna(val) or val is None:
        return val
    val_str = str(val).strip()
    if not val_str:
        return val

    try:
        num = float(val_str)
        if num > 100000000:
            return pd.to_datetime(num, unit='s', utc=True).strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        pass

    if '.' in val_str:
        try:
            return pd.to_datetime(val_str, dayfirst=True).strftime('%Y-%m-%d')
        except Exception:
            pass

    try:
        return pd.to_datetime(val_str).strftime('%Y-%m-%d')
    except Exception:
        pass

    return val_str

df['registered_at'] = df['registered_at'].apply(parse_registered_at)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)