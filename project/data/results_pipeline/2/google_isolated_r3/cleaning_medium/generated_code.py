import os
import re
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_isolated_r3/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)


def parse_date(val):
    if pd.isna(val):
        return None
    val_str = str(val).strip()
    if not val_str or val_str.lower() in ("none", "null", "nan"):
        return None

    try:
        num = float(val_str)
        if 100000000 <= num <= 2500000000:
            return pd.to_datetime(num, unit="s").strftime("%Y-%m-%d")
    except ValueError:
        pass

    if re.match(r"^\d{1,2}\.\d{1,2}\.\d{4}", val_str):
        try:
            return pd.to_datetime(
                val_str.split()[0], format="%d.%m.%Y"
            ).strftime("%Y-%m-%d")
        except Exception:
            pass

    try:
        dt = pd.to_datetime(val_str)
        if pd.notna(dt):
            return dt.strftime("%Y-%m-%d")
    except Exception:
        pass

    return None


df["registered_at"] = df["registered_at"].apply(parse_date)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)