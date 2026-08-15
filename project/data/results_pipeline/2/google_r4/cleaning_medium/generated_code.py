import os
import re
import pandas as pd

input_file = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r4/cleaning_easy/output.parquet"
output_file = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r4/cleaning_medium/output.parquet"

df = pd.read_parquet(input_file)

def parse_val(val):
    if pd.isna(val):
        return pd.NaT
    s = str(val).strip()
    if not s:
        return pd.NaT

    if re.match(r"^\d{9,11}(\.\d+)?$", s):
        try:
            return pd.to_datetime(float(s), unit="s")
        except Exception:
            pass

    if re.match(r"^\d{1,2}\.\d{1,2}\.\d{4}", s):
        try:
            return pd.to_datetime(s, format="%d.%m.%Y")
        except Exception:
            pass

    try:
        return pd.to_datetime(s)
    except Exception:
        return pd.NaT

dt_series = pd.to_datetime(df["registered_at"].apply(parse_val), errors="coerce")
df["registered_at"] = dt_series.dt.strftime("%Y-%m-%d")

os.makedirs(os.path.dirname(output_file), exist_ok=True)
df.to_parquet(output_file, index=False)