import pandas as pd
import numpy as np
import re

df = pd.read_parquet("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/anthropic/cleaning_easy/output.parquet")

def normalize_date(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    if s == "" or s.lower() == "nan":
        return None

    if re.fullmatch(r"\d{9,11}", s):
        try:
            ts = int(s)
            return pd.to_datetime(ts, unit="s").strftime("%Y-%m-%d")
        except Exception:
            pass

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        try:
            return pd.to_datetime(s, format="%Y-%m-%d").strftime("%Y-%m-%d")
        except Exception:
            pass

    if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", s):
        try:
            return pd.to_datetime(s, format="%d.%m.%Y").strftime("%Y-%m-%d")
        except Exception:
            pass

    if re.fullmatch(r"[A-Za-z]+ \d{1,2} \d{4}", s):
        try:
            return pd.to_datetime(s, format="%B %d %Y").strftime("%Y-%m-%d")
        except Exception:
            pass

    try:
        return pd.to_datetime(s).strftime("%Y-%m-%d")
    except Exception:
        return None

df["registered_at"] = df["registered_at"].apply(normalize_date)

df.to_parquet("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/anthropic/cleaning_medium/output.parquet", index=False)