import os
import re
import pandas as pd

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_easy/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_isolated/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)


def parse_val(val):
    if pd.isna(val) or val is None:
        return None
    val_str = str(val).strip()
    if not val_str or val_str.lower() in ("none", "nan", "null", "nat"):
        return None

    if re.match(r"^\d+(\.\d+)?$", val_str):
        try:
            num = float(val_str)
            if num > 100000:
                dt = pd.to_datetime(num, unit="s", errors="coerce")
                if pd.notna(dt):
                    return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    if re.match(r"^\d{1,2}\.\d{1,2}\.\d{4}$", val_str):
        try:
            dt = pd.to_datetime(val_str, format="%d.%m.%Y", errors="coerce")
            if pd.notna(dt):
                return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    try:
        dt = pd.to_datetime(val_str, errors="coerce")
        if pd.notna(dt):
            return dt.strftime("%Y-%m-%d")
    except Exception:
        pass

    return None


df["registered_at"] = df["registered_at"].apply(parse_val)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)