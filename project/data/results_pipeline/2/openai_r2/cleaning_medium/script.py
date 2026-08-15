from pathlib import Path
import pandas as pd
import numpy as np

input_path = Path(r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r2/cleaning_easy/output.parquet")
output_path = Path(r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r2/cleaning_medium/output.parquet")

df = pd.read_parquet(input_path)

raw_dates = df["registered_at"].astype("string").str.strip()
normalized_dates = pd.Series(pd.NA, index=df.index, dtype="string")

unix_mask = raw_dates.str.match(r"^-?\d{9,12}(?:\.0+)?$", na=False)
if unix_mask.any():
    unix_values = pd.to_numeric(raw_dates.loc[unix_mask], errors="coerce")
    unix_dates = pd.to_datetime(unix_values, unit="s", errors="coerce", utc=True)
    normalized_dates.loc[unix_mask] = unix_dates.dt.strftime("%Y-%m-%d").astype("string")

iso_mask = normalized_dates.isna() & raw_dates.str.match(r"^\d{4}-\d{2}-\d{2}$", na=False)
if iso_mask.any():
    iso_dates = pd.to_datetime(raw_dates.loc[iso_mask], format="%Y-%m-%d", errors="coerce")
    normalized_dates.loc[iso_mask] = iso_dates.dt.strftime("%Y-%m-%d").astype("string")

german_mask = normalized_dates.isna() & raw_dates.str.match(r"^\d{1,2}\.\d{1,2}\.\d{4}$", na=False)
if german_mask.any():
    german_dates = pd.to_datetime(raw_dates.loc[german_mask], format="%d.%m.%Y", errors="coerce")
    normalized_dates.loc[german_mask] = german_dates.dt.strftime("%Y-%m-%d").astype("string")

month_mask = normalized_dates.isna() & raw_dates.notna()
if month_mask.any():
    month_dates = pd.to_datetime(raw_dates.loc[month_mask], format="%B %d %Y", errors="coerce")
    abbreviated_mask = month_dates.isna()
    if abbreviated_mask.any():
        month_dates.loc[abbreviated_mask] = pd.to_datetime(
            raw_dates.loc[month_dates.index[abbreviated_mask]],
            format="%b %d %Y",
            errors="coerce",
        )
    normalized_dates.loc[month_mask] = month_dates.dt.strftime("%Y-%m-%d").astype("string")

unparsed_mask = normalized_dates.isna() & raw_dates.notna()
normalized_dates.loc[unparsed_mask] = raw_dates.loc[unparsed_mask]

df["registered_at"] = normalized_dates

output_path.parent.mkdir(parents=True, exist_ok=True)
df.to_parquet(output_path, index=False)