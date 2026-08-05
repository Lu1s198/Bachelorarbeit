import os
import re
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/cleaning_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)

required_columns = ["customer_id", "full_name", "email", "country", "registered_at"]
for column in required_columns:
    if column not in df.columns:
        df[column] = pd.NA

source = df["registered_at"]
text = source.astype("string").str.strip()
normalized = pd.Series(pd.NA, index=df.index, dtype="string")

unix_mask = text.str.fullmatch(r"[+-]?\d{9,11}(?:\.0+)?", na=False)
if unix_mask.any():
    unix_values = pd.to_numeric(text.loc[unix_mask], errors="coerce")
    unix_dates = pd.to_datetime(unix_values, unit="s", errors="coerce", utc=True)
    normalized.loc[unix_mask] = unix_dates.dt.strftime("%Y-%m-%d").astype("string")

iso_mask = normalized.isna() & text.str.fullmatch(r"\d{4}-\d{2}-\d{2}", na=False)
if iso_mask.any():
    iso_dates = pd.to_datetime(text.loc[iso_mask], format="%Y-%m-%d", errors="coerce")
    normalized.loc[iso_mask] = iso_dates.dt.strftime("%Y-%m-%d").astype("string")

german_mask = normalized.isna() & text.str.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{4}", na=False)
if german_mask.any():
    german_dates = pd.to_datetime(text.loc[german_mask], format="%d.%m.%Y", errors="coerce")
    normalized.loc[german_mask] = german_dates.dt.strftime("%Y-%m-%d").astype("string")

for month_format in ("%B %d %Y", "%b %d %Y", "%B %d, %Y", "%b %d, %Y"):
    mask = normalized.isna() & text.notna()
    if mask.any():
        parsed = pd.to_datetime(text.loc[mask], format=month_format, errors="coerce")
        valid = parsed.notna()
        if valid.any():
            normalized.loc[parsed.index[valid]] = parsed.loc[valid].dt.strftime("%Y-%m-%d").astype("string")

remaining_mask = normalized.isna() & text.notna()
if remaining_mask.any():
    remaining = text.loc[remaining_mask]
    parsed = pd.to_datetime(remaining, format="ISO8601", errors="coerce")
    unresolved = parsed.isna()
    if unresolved.any():
        parsed.loc[unresolved] = pd.to_datetime(
            remaining.loc[unresolved],
            format="mixed",
            errors="coerce"
        )
    valid = parsed.notna()
    if valid.any():
        normalized.loc[parsed.index[valid]] = parsed.loc[valid].dt.strftime("%Y-%m-%d").astype("string")

df["registered_at"] = normalized

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)