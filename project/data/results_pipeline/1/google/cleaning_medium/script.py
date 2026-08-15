import os
import re
import pandas as pd


def parse_date(val):
    if pd.isna(val) or val is None:
        return val
    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "null", "nat"):
        return None

    if re.match(r"^\d{9,11}(\.\d+)?$", s):
        try:
            return pd.to_datetime(float(s), unit="s").strftime("%Y-%m-%d")
        except Exception:
            pass

    if "." in s:
        try:
            return pd.to_datetime(s, dayfirst=True).strftime("%Y-%m-%d")
        except Exception:
            pass

    try:
        return pd.to_datetime(s).strftime("%Y-%m-%d")
    except Exception:
        pass

    return s


input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/cleaning_easy/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)
df["registered_at"] = df["registered_at"].apply(parse_date)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)