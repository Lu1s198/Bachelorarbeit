import os
import pandas as pd
import numpy as np

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r5/cleaning_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r5/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)

registered = df["registered_at"].astype("string").str.strip()
normalized = pd.Series(pd.NA, index=df.index, dtype="string")

epoch_mask = registered.str.fullmatch(r"[+-]?\d+(?:\.\d+)?", na=False)
if epoch_mask.any():
    epoch_values = pd.to_numeric(registered.loc[epoch_mask], errors="coerce").astype("float64")
    epoch_dates = pd.to_datetime(epoch_values, unit="s", errors="coerce", utc=True)
    normalized.loc[epoch_mask] = epoch_dates.dt.strftime("%Y-%m-%d").astype("string")

iso_mask = registered.str.fullmatch(r"\d{4}-\d{2}-\d{2}", na=False)
if iso_mask.any():
    iso_dates = pd.to_datetime(
        registered.loc[iso_mask],
        format="%Y-%m-%d",
        errors="coerce"
    )
    normalized.loc[iso_mask] = iso_dates.dt.strftime("%Y-%m-%d").astype("string")

german_mask = registered.str.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{4}", na=False)
if german_mask.any():
    german_dates = pd.to_datetime(
        registered.loc[german_mask],
        format="%d.%m.%Y",
        errors="coerce"
    )
    normalized.loc[german_mask] = german_dates.dt.strftime("%Y-%m-%d").astype("string")

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

remaining_mask = normalized.isna() & registered.notna()
if remaining_mask.any():
    parts = registered.loc[remaining_mask].str.extract(
        r"^([A-Za-z]+)\.?\s+(\d{1,2})(?:,)?\s+(\d{4})$"
    )
    month_numbers = parts[0].str.lower().map(month_map)
    valid_us_mask = month_numbers.notna()

    if valid_us_mask.any():
        us_values = (
            month_numbers.loc[valid_us_mask]
            + " "
            + parts.loc[valid_us_mask, 1]
            + " "
            + parts.loc[valid_us_mask, 2]
        )
        us_dates = pd.to_datetime(us_values, format="%m %d %Y", errors="coerce")
        normalized.loc[us_dates.index] = us_dates.dt.strftime("%Y-%m-%d").astype("string")

df["registered_at"] = normalized

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)