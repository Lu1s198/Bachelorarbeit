import pandas as pd
import numpy as np
import re
from datetime import datetime, timezone

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/cleaning_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/anthropic/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)

def normalize_date(val):
    if val is None:
        return None
    if isinstance(val, float) and np.isnan(val):
        return None
    if isinstance(val, pd.Timestamp):
        return val.strftime("%Y-%m-%d")

    s = str(val).strip()
    if s == "" or s.lower() == "nan" or s.lower() == "none":
        return None

    # Unix timestamp (all digits, possibly with sign)
    if re.match(r'^-?\d+(\.\d+)?$', s):
        try:
            ts = float(s)
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            return dt.strftime("%Y-%m-%d")
        except (ValueError, OverflowError, OSError):
            pass

    # German format DD.MM.YYYY
    m = re.match(r'^(\d{1,2})\.(\d{1,2})\.(\d{4})$', s)
    if m:
        day, month, year = m.groups()
        try:
            dt = datetime(int(year), int(month), int(day))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # US format 'Month DD YYYY'
    m = re.match(r'^([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})$', s)
    if m:
        try:
            dt = datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}", "%B %d %Y")
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            try:
                dt = datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}", "%b %d %Y")
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

    # ISO format or other parseable formats
    try:
        dt = pd.to_datetime(s, errors='raise')
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        pass

    return None

df['registered_at'] = df['registered_at'].apply(normalize_date)

df.to_parquet(output_path, index=False)