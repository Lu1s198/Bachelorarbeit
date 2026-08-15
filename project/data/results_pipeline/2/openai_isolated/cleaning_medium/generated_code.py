import os
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_isolated/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)

registered = df["registered_at"].astype("string").str.strip()
normalized = pd.Series(pd.NA, index=df.index, dtype="string")

iso_mask = registered.str.fullmatch(r"\d{4}-\d{2}-\d{2}", na=False)
if iso_mask.any():
    parsed = pd.to_datetime(registered.loc[iso_mask], format="%Y-%m-%d", errors="coerce")
    normalized.loc[iso_mask] = parsed.dt.strftime("%Y-%m-%d").astype("string")

german_mask = registered.str.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{4}", na=False)
if german_mask.any():
    parsed = pd.to_datetime(registered.loc[german_mask], format="%d.%m.%Y", errors="coerce")
    normalized.loc[german_mask] = parsed.dt.strftime("%Y-%m-%d").astype("string")

unix_mask = registered.str.fullmatch(r"[+-]?\d+", na=False)
if unix_mask.any():
    unix_values = pd.to_numeric(registered.loc[unix_mask], errors="coerce")
    parsed = pd.to_datetime(unix_values, unit="s", errors="coerce", utc=True)
    normalized.loc[unix_mask] = parsed.dt.strftime("%Y-%m-%d").astype("string")

remaining_mask = normalized.isna() & registered.notna()
if remaining_mask.any():
    parsed_full = pd.to_datetime(
        registered.loc[remaining_mask],
        format="%B %d %Y",
        errors="coerce",
    )
    normalized.loc[remaining_mask] = parsed_full.dt.strftime("%Y-%m-%d").astype("string")

still_remaining_mask = normalized.isna() & registered.notna()
if still_remaining_mask.any():
    parsed_abbr = pd.to_datetime(
        registered.loc[still_remaining_mask],
        format="%b %d %Y",
        errors="coerce",
    )
    normalized.loc[still_remaining_mask] = parsed_abbr.dt.strftime("%Y-%m-%d").astype("string")

df["registered_at"] = normalized

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)