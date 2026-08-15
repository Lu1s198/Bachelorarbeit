import os
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_isolated_r4/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)

registered = df["registered_at"].astype("string").str.strip()
parsed = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")

unix_mask = registered.str.fullmatch(r"[+-]?\d+(?:\.\d+)?", na=False)
if unix_mask.any():
    parsed.loc[unix_mask] = pd.to_datetime(
        pd.to_numeric(registered.loc[unix_mask], errors="coerce"),
        unit="s",
        errors="coerce"
    )

iso_mask = (~unix_mask) & registered.str.fullmatch(r"\d{4}-\d{2}-\d{2}", na=False)
if iso_mask.any():
    parsed.loc[iso_mask] = pd.to_datetime(
        registered.loc[iso_mask],
        format="%Y-%m-%d",
        errors="coerce"
    )

german_mask = (~unix_mask) & registered.str.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{4}", na=False)
if german_mask.any():
    parsed.loc[german_mask] = pd.to_datetime(
        registered.loc[german_mask],
        format="%d.%m.%Y",
        errors="coerce"
    )

us_mask = parsed.isna() & registered.notna() & ~unix_mask
if us_mask.any():
    parsed.loc[us_mask] = pd.to_datetime(
        registered.loc[us_mask],
        format="%B %d %Y",
        errors="coerce"
    )

df["registered_at"] = parsed.dt.strftime("%Y-%m-%d").astype("string")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)