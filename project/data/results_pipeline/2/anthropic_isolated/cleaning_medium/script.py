import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_isolated/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)

def normalize_date(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s == "" or s.lower() == "nan":
        return None

    # Unix timestamp (all digits)
    if re.fullmatch(r"\d{9,13}", s):
        try:
            ts = int(s)
            if ts > 10**11:
                ts = ts / 1000.0
            dt = datetime(1970, 1, 1) + timedelta(seconds=ts)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    # ISO format YYYY-MM-DD (possibly with time)
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    # German format TT.MM.JJJJ
    m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$", s)
    if m:
        day, month, year = m.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"

    # US format 'Month DD YYYY' or 'Month DD, YYYY'
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
                pass

    # fallback: try pandas to_datetime
    try:
        dt = pd.to_datetime(s, errors="raise")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None

df["registered_at"] = df["registered_at"].apply(normalize_date)

df.to_parquet(output_path, index=False)