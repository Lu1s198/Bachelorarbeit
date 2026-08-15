import os
import re
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_isolated_r3/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)
result = df.copy()

values = result["registered_at"].astype("string").str.strip()
normalized = pd.Series(pd.NA, index=result.index, dtype="string")

numeric_mask = values.str.fullmatch(r"[+-]?\d+(?:\.0+)?", na=False)
if numeric_mask.any():
    unix_values = pd.to_numeric(values.loc[numeric_mask], errors="coerce")
    unix_dates = pd.to_datetime(unix_values, unit="s", origin="unix", errors="coerce", utc=True)
    normalized.loc[numeric_mask] = unix_dates.dt.strftime("%Y-%m-%d").astype("string")

german_mask = values.str.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{4}", na=False)
if german_mask.any():
    german_dates = pd.to_datetime(
        values.loc[german_mask],
        format="%d.%m.%Y",
        errors="coerce"
    )
    normalized.loc[german_mask] = german_dates.dt.strftime("%Y-%m-%d").astype("string")

iso_mask = values.str.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", na=False)
if iso_mask.any():
    iso_dates = pd.to_datetime(
        values.loc[iso_mask],
        format="%Y-%m-%d",
        errors="coerce"
    )
    normalized.loc[iso_mask] = iso_dates.dt.strftime("%Y-%m-%d").astype("string")

us_mask = values.str.fullmatch(r"[A-Za-z]+ \d{1,2} \d{4}", na=False)
if us_mask.any():
    us_dates = pd.to_datetime(
        values.loc[us_mask],
        format="%B %d %Y",
        errors="coerce"
    )
    abbreviated_mask = us_dates.isna()
    if abbreviated_mask.any():
        us_dates.loc[abbreviated_mask] = pd.to_datetime(
            values.loc[us_dates.index[abbreviated_mask]],
            format="%b %d %Y",
            errors="coerce"
        )
    normalized.loc[us_mask] = us_dates.dt.strftime("%Y-%m-%d").astype("string")

remaining_mask = values.notna() & normalized.isna()
if remaining_mask.any():
    remaining_dates = pd.to_datetime(
        values.loc[remaining_mask],
        format="mixed",
        errors="coerce",
        utc=True
    )
    normalized.loc[remaining_mask] = remaining_dates.dt.strftime("%Y-%m-%d").astype("string")

result["registered_at"] = normalized

os.makedirs(os.path.dirname(output_path), exist_ok=True)
result.to_parquet(output_path, index=False)