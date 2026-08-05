import os
import re
import numpy as np
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/cleaning_easy/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)


def parse_date(val):
    if pd.isna(val):
        return None
    if isinstance(val, (pd.Timestamp, np.datetime64)):
        return pd.to_datetime(val).strftime("%Y-%m-%d")

    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "nat", "null"):
        return None

    try:
        num = float(s)
        if num > 1e7:
            return pd.to_datetime(num, unit="s").strftime("%Y-%m-%d")
    except ValueError:
        pass

    if re.search(r"^\d{1,2}\.\d{1,2}\.\d{4}", s):
        try:
            return pd.to_datetime(s, format="%d.%m.%Y").strftime("%Y-%m-%d")
        except Exception:
            pass

    try:
        return pd.to_datetime(s).strftime("%Y-%m-%d")
    except Exception:
        return None


df["registered_at"] = df["registered_at"].apply(parse_date)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)