import os
import re
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r2/cleaning_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r2/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)


def normalize_registered_at(val):
    if pd.isna(val) or val is None:
        return val
    s = str(val).strip()
    if not s:
        return s

    # 1. Unix timestamp (seconds)
    try:
        num = float(s)
        if 1e8 <= num <= 3e9:
            return pd.to_datetime(num, unit="s", utc=True).strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        pass

    # 2. German format (TT.MM.JJJJ)
    if "." in s and not re.search(r"[a-zA-Z]", s):
        try:
            return pd.to_datetime(s, dayfirst=True).strftime("%Y-%m-%d")
        except Exception:
            pass

    # 3. General ISO or US format ('Month DD YYYY', 'YYYY-MM-DD', etc.)
    try:
        return pd.to_datetime(s).strftime("%Y-%m-%d")
    except Exception:
        return s


df["registered_at"] = df["registered_at"].apply(normalize_registered_at)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)