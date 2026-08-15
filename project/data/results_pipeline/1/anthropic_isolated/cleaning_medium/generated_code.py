import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta

df = pd.read_parquet("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/_reference/cleaning_easy/output.parquet")

def normalize_date(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s == "" or s.lower() == "nan":
        return None

    # Unix timestamp (all digits)
    if re.fullmatch(r"\d{9,10}", s):
        try:
            dt = datetime(1970, 1, 1) + timedelta(seconds=int(s))
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    # ISO format YYYY-MM-DD
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    # German format DD.MM.YYYY
    m = re.fullmatch(r"(\d{2})\.(\d{2})\.(\d{4})", s)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"

    # US format Month DD YYYY
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

    # Fallback: try pandas to_datetime
    try:
        dt = pd.to_datetime(s)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None

df["registered_at"] = df["registered_at"].apply(normalize_date)

df.to_parquet("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic_isolated/cleaning_medium/output.parquet", index=False)