import os
import re
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/openai/cleaning_easy/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/openai/cleaning_medium/output.parquet"

df = pd.read_parquet(input_path)

values = df["registered_at"].astype("string").str.strip()
normalized = pd.Series(pd.NA, index=df.index, dtype="string")

iso_mask = values.str.fullmatch(r"\d{4}-\d{2}-\d{2}", na=False)
if iso_mask.any():
    parsed = pd.to_datetime(values.loc[iso_mask], format="%Y-%m-%d", errors="coerce")
    normalized.loc[iso_mask] = parsed.dt.strftime("%Y-%m-%d").astype("string")

german_mask = values.str.fullmatch(r"\d{2}\.\d{2}\.\d{4}", na=False)
if german_mask.any():
    parsed = pd.to_datetime(values.loc[german_mask], format="%d.%m.%Y", errors="coerce")
    normalized.loc[german_mask] = parsed.dt.strftime("%Y-%m-%d").astype("string")

us_mask = values.str.fullmatch(r"[A-Za-z]+ \d{1,2} \d{4}", na=False)
if us_mask.any():
    parsed = pd.to_datetime(values.loc[us_mask], format="%B %d %Y", errors="coerce")
    normalized.loc[us_mask] = parsed.dt.strftime("%Y-%m-%d").astype("string")

us_comma_mask = values.str.fullmatch(r"[A-Za-z]+ \d{1,2}, \d{4}", na=False)
if us_comma_mask.any():
    parsed = pd.to_datetime(values.loc[us_comma_mask], format="%B %d, %Y", errors="coerce")
    normalized.loc[us_comma_mask] = parsed.dt.strftime("%Y-%m-%d").astype("string")

unix_mask = values.str.fullmatch(r"[+-]?\d{9,12}", na=False)
if unix_mask.any():
    numeric_values = pd.to_numeric(values.loc[unix_mask], errors="coerce")
    parsed = pd.to_datetime(numeric_values, unit="s", errors="coerce")
    normalized.loc[unix_mask] = parsed.dt.strftime("%Y-%m-%d").astype("string")

df["registered_at"] = normalized

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)