import os
import re
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google/cleaning_easy/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)


def convert_date(val):
    if pd.isna(val) or val is None:
        return val
    s = str(val).strip()
    if not s:
        return s

    if re.match(r"^\d+(\.\d+)?$", s):
        try:
            num = float(s)
            if num > 315360000:
                return pd.to_datetime(num, unit="s", utc=True).strftime(
                    "%Y-%m-%d"
                )
        except Exception:
            pass

    try:
        dt = pd.to_datetime(s, dayfirst=True, format="mixed")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        pass

    try:
        dt = pd.to_datetime(s)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return s


df["registered_at"] = df["registered_at"].apply(convert_date)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)