import pandas as pd
import numpy as np
from datetime import datetime, timezone

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r5/cleaning_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r5/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)

def normalize_date(val):
    if val is None:
        return None
    s = str(val).strip()
    if s == "" or s.lower() == "nan" or s.lower() == "none":
        return None

    # Unix timestamp (seconds) - all digits
    if s.isdigit():
        try:
            ts = int(s)
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    # ISO format YYYY-MM-DD
    try:
        dt = datetime.strptime(s, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass

    # German format DD.MM.YYYY
    try:
        dt = datetime.strptime(s, "%d.%m.%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass

    # US format 'Month DD YYYY'
    try:
        dt = datetime.strptime(s, "%B %d %Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass

    # Try ISO with time component
    try:
        dt = datetime.fromisoformat(s)
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass

    return None

df["registered_at"] = df["registered_at"].apply(normalize_date)

df.to_parquet(output_path, index=False)