import os
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r3/cleaning_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r3/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)

raw_dates = df["registered_at"].astype("string").str.strip()
parsed_dates = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")

unix_mask = raw_dates.str.fullmatch(r"-?\d{9,}(?:\.\d+)?", na=False)
if unix_mask.any():
    unix_values = pd.to_numeric(raw_dates.loc[unix_mask], errors="coerce")
    unix_dates = pd.to_datetime(unix_values, unit="s", errors="coerce", utc=True).dt.tz_localize(None)
    parsed_dates.loc[unix_mask] = unix_dates

remaining_mask = parsed_dates.isna() & raw_dates.notna()

if remaining_mask.any():
    iso_dates = pd.to_datetime(
        raw_dates.loc[remaining_mask],
        format="ISO8601",
        errors="coerce"
    )
    parsed_dates.loc[remaining_mask] = iso_dates

remaining_mask = parsed_dates.isna() & raw_dates.notna()
if remaining_mask.any():
    german_dates = pd.to_datetime(
        raw_dates.loc[remaining_mask],
        format="%d.%m.%Y",
        errors="coerce"
    )
    parsed_dates.loc[remaining_mask] = german_dates

remaining_mask = parsed_dates.isna() & raw_dates.notna()
if remaining_mask.any():
    us_dates = pd.to_datetime(
        raw_dates.loc[remaining_mask],
        format="%B %d %Y",
        errors="coerce"
    )
    parsed_dates.loc[remaining_mask] = us_dates

remaining_mask = parsed_dates.isna() & raw_dates.notna()
if remaining_mask.any():
    us_abbrev_dates = pd.to_datetime(
        raw_dates.loc[remaining_mask],
        format="%b %d %Y",
        errors="coerce"
    )
    parsed_dates.loc[remaining_mask] = us_abbrev_dates

df["registered_at"] = parsed_dates.dt.strftime("%Y-%m-%d").astype("string")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)