import os
import re
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/_reference/cleaning_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai_isolated/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)

values = df["registered_at"].astype("string").str.strip()
parsed = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")

unix_mask = values.str.fullmatch(r"[+-]?\d{9,12}", na=False)
if unix_mask.any():
    unix_values = pd.to_numeric(values.loc[unix_mask], errors="coerce")
    parsed.loc[unix_mask] = pd.to_datetime(unix_values, unit="s", errors="coerce")

german_mask = values.str.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{4}", na=False)
if german_mask.any():
    parsed.loc[german_mask] = pd.to_datetime(
        values.loc[german_mask],
        format="%d.%m.%Y",
        errors="coerce"
    )

iso_mask = values.str.fullmatch(r"\d{4}-\d{2}-\d{2}", na=False)
if iso_mask.any():
    parsed.loc[iso_mask] = pd.to_datetime(
        values.loc[iso_mask],
        format="%Y-%m-%d",
        errors="coerce"
    )

remaining_mask = parsed.isna() & values.notna() & values.ne("")
if remaining_mask.any():
    remaining = values.loc[remaining_mask]
    us_parsed = pd.to_datetime(remaining, format="%B %d %Y", errors="coerce")
    missing_us = us_parsed.isna()
    if missing_us.any():
        us_parsed.loc[missing_us] = pd.to_datetime(
            remaining.loc[missing_us],
            format="%b %d %Y",
            errors="coerce"
        )
    parsed.loc[remaining_mask] = us_parsed

df["registered_at"] = parsed.dt.strftime("%Y-%m-%d").astype("string")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)