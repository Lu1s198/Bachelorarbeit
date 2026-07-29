import pandas as pd
import numpy as np
import re
from datetime import datetime

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/cleaning_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)

def normalize_date(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s == "" or s.lower() == "nan" or s.lower() == "none":
        return None

    # Unix timestamp (all digits, possibly with decimal)
    if re.fullmatch(r"\d{9,10}(\.\d+)?", s):
        try:
            ts = float(s)
            dt = datetime.utcfromtimestamp(ts)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    # ISO format YYYY-MM-DD (possibly with time)
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    # German format DD.MM.YYYY
    m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$", s)
    if m:
        day, month, year = m.groups()
        try:
            dt = datetime(int(year), int(month), int(day))
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return None

    # US format 'Month DD YYYY' e.g. January 05 2020
    m = re.match(r"^([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})$", s)
    if m:
        month_name, day, year = m.groups()
        try:
            dt = datetime.strptime(f"{month_name} {day} {year}", "%B %d %Y")
            return dt.strftime("%Y-%m-%d")
        except Exception:
            try:
                dt = datetime.strptime(f"{month_name} {day} {year}", "%b %d %Y")
                return dt.strftime("%Y-%m-%d")
            except Exception:
                return None

    # Fallback: try pandas to_datetime
    try:
        dt = pd.to_datetime(s, errors="coerce")
        if pd.notna(dt):
            return dt.strftime("%Y-%m-%d")
    except Exception:
        pass

    return None

df["registered_at"] = df["registered_at"].apply(normalize_date)

df.to_parquet(output_path, index=False)