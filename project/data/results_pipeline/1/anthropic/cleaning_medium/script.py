import pandas as pd
import numpy as np
import re
from datetime import datetime

df = pd.read_parquet("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/cleaning_easy/output.parquet")

def normalize_date(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s == "" or s.lower() == "none" or s.lower() == "nan":
        return None

    # Unix timestamp (seconds) - all digits
    if re.fullmatch(r"\d{9,10}", s):
        try:
            dt = datetime.utcfromtimestamp(int(s))
            return dt.strftime("%Y-%m-%d")
        except (ValueError, OSError, OverflowError):
            pass

    # ISO format YYYY-MM-DD
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return s

    # German format TT.MM.JJJJ
    m = re.fullmatch(r"(\d{2})\.(\d{2})\.(\d{4})", s)
    if m:
        day, month, year = m.groups()
        return f"{year}-{month}-{day}"

    # US format 'Month DD YYYY' or 'Month DD, YYYY'
    m = re.fullmatch(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})", s)
    if m:
        month_name, day, year = m.groups()
        try:
            dt = datetime.strptime(f"{month_name} {day} {year}", "%B %d %Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            try:
                dt = datetime.strptime(f"{month_name} {day} {year}", "%b %d %Y")
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

    # Fallback: try pandas to_datetime
    try:
        dt = pd.to_datetime(s, errors="raise")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None

df["registered_at"] = df["registered_at"].apply(normalize_date)

df.to_parquet("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/cleaning_medium/output.parquet", index=False)