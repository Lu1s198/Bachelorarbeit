import os
import re
from datetime import date, datetime

import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/cleaning_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/cleaning_medium/output.parquet"

month_mapping = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "aug": 8, "sep": 9,
    "sept": 9, "oct": 10, "nov": 11, "dec": 12,
}

iso_pattern = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(?:[T\s].*)?$")
german_pattern = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$")
us_pattern = re.compile(r"^([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})$")
unix_pattern = re.compile(r"^[+-]?\d+(?:\.\d+)?$")


def format_date(year, month, day):
    try:
        return date(int(year), int(month), int(day)).isoformat()
    except (TypeError, ValueError, OverflowError):
        return pd.NA


def normalize_registered_at(value):
    if value is None or value is pd.NA:
        return pd.NA

    try:
        if bool(pd.isna(value)):
            return pd.NA
    except (TypeError, ValueError):
        pass

    if isinstance(value, (pd.Timestamp, np.datetime64, datetime, date)):
        timestamp = pd.Timestamp(value)
        if pd.isna(timestamp):
            return pd.NA
        return timestamp.date().isoformat()

    if isinstance(value, (int, float, np.integer, np.floating)) and not isinstance(value, bool):
        timestamp = pd.to_datetime(value, unit="s", utc=True, errors="coerce")
        if pd.isna(timestamp):
            return pd.NA
        return timestamp.date().isoformat()

    text = str(value).strip()
    if not text:
        return pd.NA

    if unix_pattern.fullmatch(text):
        timestamp = pd.to_datetime(float(text), unit="s", utc=True, errors="coerce")
        if pd.isna(timestamp):
            return pd.NA
        return timestamp.date().isoformat()

    match = iso_pattern.fullmatch(text)
    if match:
        return format_date(match.group(1), match.group(2), match.group(3))

    match = german_pattern.fullmatch(text)
    if match:
        return format_date(match.group(3), match.group(2), match.group(1))

    match = us_pattern.fullmatch(text)
    if match:
        month = month_mapping.get(match.group(1).lower())
        if month is not None:
            return format_date(match.group(3), month, match.group(2))

    return pd.NA


df = pd.read_parquet(input_path)

required_columns = ["customer_id", "full_name", "email", "country", "registered_at"]
missing_columns = [column for column in required_columns if column not in df.columns]
if missing_columns:
    raise ValueError(f"Missing required columns: {missing_columns}")

df["registered_at"] = df["registered_at"].map(normalize_registered_at).astype("string")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)