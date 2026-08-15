import pandas as pd
import numpy as np
import re

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/cleaning_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)

def normalize_date(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s == "" or s.lower() == "nan":
        return None

    # Unix timestamp (all digits, optionally with decimal point)
    if re.fullmatch(r"\d+(\.\d+)?", s):
        try:
            ts = float(s)
            dt = pd.to_datetime(ts, unit='s')
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    # ISO format YYYY-MM-DD (possibly with time)
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        try:
            dt = pd.to_datetime(s, format="%Y-%m-%d", errors='raise')
            return dt.strftime("%Y-%m-%d")
        except Exception:
            try:
                dt = pd.to_datetime(s)
                return dt.strftime("%Y-%m-%d")
            except Exception:
                pass

    # German format DD.MM.YYYY
    m = re.match(r"^(\d{2})\.(\d{2})\.(\d{4})$", s)
    if m:
        try:
            dt = pd.to_datetime(s, format="%d.%m.%Y", errors='raise')
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    # US format 'Month DD YYYY' e.g. "January 05 2020"
    m = re.match(r"^[A-Za-z]+\s+\d{1,2}\s+\d{4}$", s)
    if m:
        try:
            dt = pd.to_datetime(s, format="%B %d %Y", errors='raise')
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    # Fallback: try generic parsing
    try:
        dt = pd.to_datetime(s, errors='raise')
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None

df["registered_at"] = df["registered_at"].apply(normalize_date)

df.to_parquet(output_path, index=False)