import os
import re
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/_reference/cleaning_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/openai_isolated/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)

registered = df["registered_at"].astype("string").str.strip()
parsed = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")

iso_mask = registered.str.fullmatch(r"\d{4}-\d{2}-\d{2}", na=False)
parsed.loc[iso_mask] = pd.to_datetime(
    registered.loc[iso_mask],
    format="%Y-%m-%d",
    errors="coerce"
)

german_mask = registered.str.fullmatch(r"\d{1,2}\.\d{1,2}\.\d{4}", na=False)
parsed.loc[german_mask] = pd.to_datetime(
    registered.loc[german_mask],
    format="%d.%m.%Y",
    errors="coerce"
)

unix_mask = registered.str.fullmatch(r"[+-]?\d+", na=False)
if unix_mask.any():
    unix_values = pd.to_numeric(registered.loc[unix_mask], errors="coerce")
    parsed.loc[unix_mask] = pd.to_datetime(unix_values, unit="s", errors="coerce")

remaining_mask = parsed.isna() & registered.notna() & ~unix_mask
if remaining_mask.any():
    us_values = registered.loc[remaining_mask].str.replace(",", "", regex=False)
    parsed.loc[remaining_mask] = pd.to_datetime(
        us_values,
        format="mixed",
        errors="coerce",
        dayfirst=False
    )

df["registered_at"] = parsed.dt.strftime("%Y-%m-%d").astype("string")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)