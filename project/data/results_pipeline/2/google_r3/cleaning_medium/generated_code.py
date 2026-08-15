import os
import re
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r3/cleaning_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r3/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)

def parse_date(val):
    if pd.isna(val) or val is None:
        return None
    val_str = str(val).strip()
    if not val_str:
        return None

    if re.match(r'^\d+(\.\d+)?$', val_str):
        try:
            num = float(val_str)
            if num > 100000000:
                return pd.to_datetime(num, unit='s', utc=True).tz_localize(None).strftime('%Y-%m-%d')
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
        return pd.to_datetime(val_str).strftime('%Y-%m-%d')
    except Exception:
        pass

    return val_str

df['registered_at'] = df['registered_at'].apply(parse_date)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)