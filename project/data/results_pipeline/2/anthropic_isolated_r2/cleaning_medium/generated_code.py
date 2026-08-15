import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_isolated_r2/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)

def normalize_date(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s == "" or s.lower() == "nan":
        return None

    # Unix timestamp (all digits)
    if re.fullmatch(r"\d+", s):
        try:
            ts = int(s)
            dt = datetime(1970, 1, 1) + timedelta(seconds=ts)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    # ISO format YYYY-MM-DD (possibly with time)
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        try:
            dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    # German format DD.MM.YYYY
    m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$", s)
    if m:
        try:
            dt = datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    # US format 'Month DD YYYY'
    try:
        dt = datetime.strptime(s, "%B %d %Y")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        pass

    try:
        dt = datetime.strptime(s, "%b %d %Y")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        pass

    # Fallback: try pandas parser
    try:
        dt = pd.to_datetime(s, errors="coerce")
        if pd.notna(dt):
            return dt.strftime("%Y-%m-%d")
    except Exception:
        pass

    return None

df["registered_at"] = df["registered_at"].apply(normalize_date)

df.to_parquet(output_path, index=False)