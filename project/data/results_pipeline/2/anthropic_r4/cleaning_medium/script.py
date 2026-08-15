import pandas as pd
import numpy as np
import re
from datetime import datetime, timezone

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r4/cleaning_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r4/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)

def normalize_date(val):
    if val is None:
        return None
    s = str(val).strip()
    if s == "" or s.lower() == "nan" or s.lower() == "none":
        return None

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return s

    if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", s):
        try:
            dt = datetime.strptime(s, "%d.%m.%Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return None

    if re.fullmatch(r"[A-Za-z]+ \d{1,2} \d{4}", s):
        try:
            dt = datetime.strptime(s, "%B %d %Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            try:
                dt = datetime.strptime(s, "%b %d %Y")
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                return None

    if re.fullmatch(r"\d+(\.\d+)?", s):
        try:
            ts = float(s)
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            return dt.strftime("%Y-%m-%d")
        except (ValueError, OSError, OverflowError):
            return None

    try:
        dt = pd.to_datetime(s)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None

df["registered_at"] = df["registered_at"].apply(normalize_date)

df.to_parquet(output_path, index=False)