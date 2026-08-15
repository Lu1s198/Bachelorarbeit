import os
import re
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/cleaning_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)

raw_dates = df["registered_at"].astype("string").str.strip()
parsed_dates = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")

iso_mask = raw_dates.str.fullmatch(r"\d{4}-\d{2}-\d{2}", na=False)
parsed_dates.loc[iso_mask] = pd.to_datetime(
    raw_dates.loc[iso_mask],
    format="%Y-%m-%d",
    errors="coerce"
)

german_mask = raw_dates.str.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{4}", na=False)
parsed_dates.loc[german_mask] = pd.to_datetime(
    raw_dates.loc[german_mask],
    format="%d.%m.%Y",
    errors="coerce"
)

us_long_mask = raw_dates.str.fullmatch(
    r"[A-Za-z]+\s+\d{1,2},?\s+\d{4}",
    na=False
)
if us_long_mask.any():
    us_values = raw_dates.loc[us_long_mask].str.replace(",", "", regex=False)
    parsed_us = pd.to_datetime(us_values, format="%B %d %Y", errors="coerce")
    failed_us_mask = parsed_us.isna()
    if failed_us_mask.any():
        parsed_us.loc[failed_us_mask] = pd.to_datetime(
            us_values.loc[failed_us_mask],
            format="%b %d %Y",
            errors="coerce"
        )
    parsed_dates.loc[us_long_mask] = parsed_us

unix_mask = raw_dates.str.fullmatch(r"[+-]?\d+(?:\.0+)?", na=False)
if unix_mask.any():
    unix_values = pd.to_numeric(raw_dates.loc[unix_mask], errors="coerce")
    parsed_dates.loc[unix_mask] = pd.to_datetime(
        unix_values,
        unit="s",
        errors="coerce"
    )

df["registered_at"] = parsed_dates.dt.strftime("%Y-%m-%d").astype("string")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)