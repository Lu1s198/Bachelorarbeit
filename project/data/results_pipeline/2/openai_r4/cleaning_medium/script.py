import os
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r4/cleaning_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r4/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)

raw = df["registered_at"].astype("string").str.strip()
parsed = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")

unix_mask = raw.str.fullmatch(r"[+-]?\d+(?:\.\d+)?", na=False)
iso_mask = raw.str.fullmatch(r"\d{4}-\d{2}-\d{2}", na=False)
german_mask = raw.str.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{4}", na=False)
us_mask = raw.str.fullmatch(r"[A-Za-z]+ \d{1,2} \d{4}", na=False)

if unix_mask.any():
    unix_values = pd.to_numeric(raw.loc[unix_mask], errors="coerce")
    parsed.loc[unix_mask] = pd.to_datetime(unix_values, unit="s", errors="coerce")

if iso_mask.any():
    parsed.loc[iso_mask] = pd.to_datetime(
        raw.loc[iso_mask],
        format="%Y-%m-%d",
        errors="coerce"
    )

if german_mask.any():
    parsed.loc[german_mask] = pd.to_datetime(
        raw.loc[german_mask],
        format="%d.%m.%Y",
        errors="coerce"
    )

if us_mask.any():
    parsed.loc[us_mask] = pd.to_datetime(
        raw.loc[us_mask],
        format="%B %d %Y",
        errors="coerce"
    )

remaining_mask = raw.notna() & parsed.isna()
if remaining_mask.any():
    parsed.loc[remaining_mask] = pd.to_datetime(
        raw.loc[remaining_mask],
        format="mixed",
        errors="coerce"
    )

df["registered_at"] = parsed.dt.strftime("%Y-%m-%d").astype("string")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)