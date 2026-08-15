import os
import re
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_easy/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_isolated_r2/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)


def normalize_registered_at(val):
    if pd.isna(val) or val is None:
        return None
    s = str(val).strip()
    if not s:
        return None

    if re.match(r"^\d{1,2}\.\d{1,2}\.\d{4}$", s):
        parts = s.split(".")
        return f"{int(parts[2]):04d}-{int(parts[1]):02d}-{int(parts[0]):02d}"

    if re.match(r"^\d{9,11}(\.\d+)?$", s):
        try:
            dt = pd.to_datetime(float(s), unit="s", utc=True)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    try:
        dt = pd.to_datetime(s, errors="coerce")
        if pd.notna(dt):
            return dt.strftime("%Y-%m-%d")
    except Exception:
        pass

    return s


df["registered_at"] = df["registered_at"].apply(normalize_registered_at)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)