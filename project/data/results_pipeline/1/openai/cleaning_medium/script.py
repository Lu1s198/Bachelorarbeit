import os
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/cleaning_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)

if "registered_at" in df.columns:
    raw = df["registered_at"]
    text = raw.astype("string").str.strip()
    result = pd.Series(pd.NA, index=df.index, dtype="string")

    numeric_values = pd.to_numeric(text, errors="coerce")
    unix_mask = numeric_values.notna() & numeric_values.between(100000000, 9999999999)

    if unix_mask.any():
        unix_dates = pd.to_datetime(
            numeric_values.loc[unix_mask],
            unit="s",
            utc=True,
            errors="coerce"
        )
        result.loc[unix_mask] = unix_dates.dt.strftime("%Y-%m-%d").astype("string")

    iso_mask = (~unix_mask) & text.str.match(r"^\d{4}-\d{1,2}-\d{1,2}$", na=False)
    if iso_mask.any():
        iso_dates = pd.to_datetime(
            text.loc[iso_mask],
            format="%Y-%m-%d",
            errors="coerce"
        )
        result.loc[iso_mask] = iso_dates.dt.strftime("%Y-%m-%d").astype("string")

    german_mask = (~unix_mask) & text.str.match(r"^\d{1,2}\.\d{1,2}\.\d{4}$", na=False)
    if german_mask.any():
        german_dates = pd.to_datetime(
            text.loc[german_mask],
            format="%d.%m.%Y",
            errors="coerce"
        )
        result.loc[german_mask] = german_dates.dt.strftime("%Y-%m-%d").astype("string")

    remaining_mask = ~(unix_mask | iso_mask | german_mask) & text.notna()
    if remaining_mask.any():
        remaining_dates = pd.to_datetime(
            text.loc[remaining_mask],
            errors="coerce"
        )
        result.loc[remaining_mask] = remaining_dates.dt.strftime("%Y-%m-%d").astype("string")

    df["registered_at"] = result

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)