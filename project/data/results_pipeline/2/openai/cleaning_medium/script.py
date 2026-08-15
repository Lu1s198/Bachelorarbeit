import os
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai/cleaning_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)

values = df["registered_at"].astype("string").str.strip()
normalized = pd.Series(pd.NA, index=df.index, dtype="string")

def set_formatted_dates(mask, parsed):
    formatted = parsed.dt.strftime("%Y-%m-%d").astype("string")
    normalized.loc[mask] = formatted

unix_mask = values.str.fullmatch(r"-?\d{9,11}(?:\.0+)?", na=False)
if unix_mask.any():
    unix_values = pd.to_numeric(values.loc[unix_mask], errors="coerce")
    unix_dates = pd.to_datetime(unix_values, unit="s", utc=True, errors="coerce")
    set_formatted_dates(unix_mask, unix_dates)

iso_mask = values.str.fullmatch(r"\d{4}-\d{2}-\d{2}", na=False) & ~unix_mask
if iso_mask.any():
    iso_dates = pd.to_datetime(
        values.loc[iso_mask],
        format="%Y-%m-%d",
        errors="coerce"
    )
    set_formatted_dates(iso_mask, iso_dates)

german_mask = values.str.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{4}", na=False)
if german_mask.any():
    german_dates = pd.to_datetime(
        values.loc[german_mask],
        format="%d.%m.%Y",
        errors="coerce"
    )
    set_formatted_dates(german_mask, german_dates)

month_map = {
    "january": "01",
    "february": "02",
    "march": "03",
    "april": "04",
    "may": "05",
    "june": "06",
    "july": "07",
    "august": "08",
    "september": "09",
    "october": "10",
    "november": "11",
    "december": "12",
    "jan": "01",
    "feb": "02",
    "mar": "03",
    "apr": "04",
    "jun": "06",
    "jul": "07",
    "aug": "08",
    "sep": "09",
    "sept": "09",
    "oct": "10",
    "nov": "11",
    "dec": "12",
}

us_pattern = (
    r"(?i)^(january|february|march|april|may|june|july|august|september|october|"
    r"november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)"
    r"\s+(\d{1,2})(?:,)?\s+(\d{4})$"
)
us_mask = values.str.fullmatch(us_pattern, na=False)
if us_mask.any():
    parts = values.loc[us_mask].str.extract(us_pattern, flags=0)
    month_numbers = parts[0].str.lower().map(month_map).astype("string")
    day_numbers = parts[1].astype("string").str.zfill(2)
    years = parts[2].astype("string")
    us_dates_text = years + "-" + month_numbers + "-" + day_numbers
    us_dates = pd.to_datetime(us_dates_text, format="%Y-%m-%d", errors="coerce")
    set_formatted_dates(us_mask, us_dates)

df["registered_at"] = normalized

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)