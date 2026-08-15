import os
import re
import numpy as np
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/_reference/cleaning_easy/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/google_isolated/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)

def parse_val(val):
    if pd.isna(val) or val is None:
        return np.nan
    s = str(val).strip()
    if not s:
        return np.nan

    if re.fullmatch(r"\d{9,11}(\.\d+)?", s):
        try:
            dt = pd.to_datetime(float(s), unit="s", errors="coerce")
            if pd.notna(dt):
                return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    if re.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{4}", s):
        try:
            dt = pd.to_datetime(s, format="%d.%m.%Y", errors="coerce")
            if pd.notna(dt):
                return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    try:
        dt = pd.to_datetime(s, errors="coerce")
        if pd.notna(dt):
            return dt.strftime("%Y-%m-%d")
    except Exception:
        pass

    return np.nan

df["registered_at"] = df["registered_at"].apply(parse_val)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)