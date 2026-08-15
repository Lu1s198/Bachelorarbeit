import pandas as pd
import numpy as np
import re
from datetime import datetime, timezone

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r3/cleaning_easy/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r3/cleaning_medium/output.parquet"

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
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return None

    # ISO format YYYY-MM-DD
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return s

    # German format TT.MM.JJJJ
    m = re.fullmatch(r"(\d{2})\.(\d{2})\.(\d{4})", s)
    if m:
        day, month, year = m.groups()
        return f"{year}-{month}-{day}"

    # US format 'Month DD YYYY'
    try:
        dt = datetime.strptime(s, "%B %d %Y")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        pass

    # Try generic parsing as fallback
    try:
        dt = pd.to_datetime(s, errors="coerce")
        if pd.notna(dt):
            return dt.strftime("%Y-%m-%d")
    except Exception:
        pass

    return None

df["registered_at"] = df["registered_at"].apply(normalize_date)

df.to_parquet(output_path, index=False)