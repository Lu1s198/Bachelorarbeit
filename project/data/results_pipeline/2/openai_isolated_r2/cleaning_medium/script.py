import os
import re
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_isolated_r2/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)

values = df["registered_at"].astype("string").str.strip()
parsed = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")

iso_mask = values.str.match(r"^\d{4}-\d{2}-\d{2}$", na=False)
parsed.loc[iso_mask] = pd.to_datetime(
    values.loc[iso_mask],
    format="%Y-%m-%d",
    errors="coerce"
)

german_mask = values.str.match(r"^\d{1,2}\.\d{1,2}\.\d{4}$", na=False)
parsed.loc[german_mask] = pd.to_datetime(
    values.loc[german_mask],
    format="%d.%m.%Y",
    errors="coerce"
)

month_mapping = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}

month_parts = values.str.extract(
    r"^(?P<month>[A-Za-z]+)\s+(?P<day>\d{1,2}),?\s+(?P<year>\d{4})$"
)
month_numbers = month_parts["month"].str.casefold().map(month_mapping)
us_mask = month_numbers.notna()

if us_mask.any():
    us_dates = (
        month_numbers.loc[us_mask].astype("Int64").astype("string").str.zfill(2)
        + "-"
        + month_parts.loc[us_mask, "day"].astype("string").str.zfill(2)
        + "-"
        + month_parts.loc[us_mask, "year"].astype("string")
    )
    parsed.loc[us_mask] = pd.to_datetime(
        us_dates,
        format="%m-%d-%Y",
        errors="coerce"
    )

unix_mask = values.str.match(r"^-?\d+(?:\.\d+)?$", na=False)
if unix_mask.any():
    unix_values = pd.to_numeric(values.loc[unix_mask], errors="coerce")
    parsed.loc[unix_mask] = pd.to_datetime(
        unix_values,
        unit="s",
        errors="coerce"
    )

remaining_mask = parsed.isna() & values.notna() & values.ne("")
if remaining_mask.any():
    parsed.loc[remaining_mask] = pd.to_datetime(
        values.loc[remaining_mask],
        format="mixed",
        errors="coerce"
    )

df["registered_at"] = parsed.dt.strftime("%Y-%m-%d").astype("string")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)