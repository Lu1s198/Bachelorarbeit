import os
import re
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_easy/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_isolated_r5/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)


def convert_date(val):
    if pd.isna(val) or val is None:
        return val
    val_str = str(val).strip()
    if not val_str:
        return val

    if re.match(r"^\d{1,2}\.\d{1,2}\.\d{4}", val_str):
        dt = pd.to_datetime(val_str, format="%d.%m.%Y", errors="coerce")
        if pd.notna(dt):
            return dt.strftime("%Y-%m-%d")

    if re.match(r"^\d{9,11}(\.\d+)?$", val_str):
        try:
            dt = pd.to_datetime(float(val_str), unit="s", errors="coerce")
            if pd.notna(dt):
                return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    dt = pd.to_datetime(val_str, errors="coerce")
    if pd.notna(dt):
        return dt.strftime("%Y-%m-%d")

    return val_str


df["registered_at"] = df["registered_at"].apply(convert_date)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)