import os
from pathlib import Path

import numpy as np
import pandas as pd

input_path = Path(r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_easy/output.parquet")
output_path = Path(r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_isolated_r5/cleaning_medium/output.parquet")

df = pd.read_parquet(input_path)

registered = df["registered_at"].astype("string").str.strip()
normalized = pd.Series(pd.NA, index=df.index, dtype="string")

unix_mask = registered.str.fullmatch(r"[+-]?\d+(?:\.0+)?", na=False)
if unix_mask.any():
    unix_values = pd.to_numeric(registered.loc[unix_mask], errors="coerce")
    unix_dates = pd.to_datetime(unix_values, unit="s", errors="coerce", utc=True)
    normalized.loc[unix_mask] = unix_dates.dt.strftime("%Y-%m-%d").astype("string")

iso_mask = registered.str.fullmatch(r"\d{4}-\d{2}-\d{2}", na=False)
if iso_mask.any():
    iso_dates = pd.to_datetime(
        registered.loc[iso_mask],
        format="%Y-%m-%d",
        errors="coerce",
    )
    normalized.loc[iso_mask] = iso_dates.dt.strftime("%Y-%m-%d").astype("string")

iso_datetime_mask = registered.str.match(r"^\d{4}-\d{2}-\d{2}[T\s]", na=False)
if iso_datetime_mask.any():
    iso_datetime_dates = pd.to_datetime(
        registered.loc[iso_datetime_mask],
        format="ISO8601",
        errors="coerce",
    )
    normalized.loc[iso_datetime_mask] = iso_datetime_dates.dt.strftime("%Y-%m-%d").astype("string")

german_mask = registered.str.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{4}", na=False)
if german_mask.any():
    german_dates = pd.to_datetime(
        registered.loc[german_mask],
        format="%d.%m.%Y",
        errors="coerce",
    )
    normalized.loc[german_mask] = german_dates.dt.strftime("%Y-%m-%d").astype("string")

remaining_mask = normalized.isna() & registered.notna()
if remaining_mask.any():
    us_values = registered.loc[remaining_mask].str.replace(",", "", regex=False)
    parsed_us = pd.Series(pd.NaT, index=us_values.index, dtype="datetime64[us]")

    for date_format in ("%B %d %Y", "%b %d %Y"):
        unresolved = parsed_us.isna()
        if unresolved.any():
            parsed_us.loc[unresolved] = pd.to_datetime(
                us_values.loc[unresolved],
                format=date_format,
                errors="coerce",
            )

    normalized.loc[remaining_mask] = parsed_us.dt.strftime("%Y-%m-%d").astype("string")

df["registered_at"] = normalized

os.makedirs(output_path.parent, exist_ok=True)
df.to_parquet(output_path, index=False)