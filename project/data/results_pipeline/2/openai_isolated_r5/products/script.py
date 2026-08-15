import os
import re
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_isolated_r5/products/output.parquet"

df = pd.read_csv(input_path)

def parse_price(value):
    if pd.isna(value):
        return np.nan

    text = str(value).strip()
    text = re.sub(r"(?i)(eur|€)", "", text)
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[^0-9,.\-+]", "", text)

    if not text or text in {"-", "+", ".", ","}:
        return np.nan

    comma_count = text.count(",")
    dot_count = text.count(".")

    if comma_count and dot_count:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif comma_count:
        if comma_count == 1:
            text = text.replace(",", ".")
        else:
            parts = text.split(",")
            if len(parts[-1]) in (1, 2):
                text = "".join(parts[:-1]) + "." + parts[-1]
            else:
                text = "".join(parts)
    elif dot_count > 1:
        parts = text.split(".")
        if len(parts[-1]) in (1, 2):
            text = "".join(parts[:-1]) + "." + parts[-1]
        else:
            text = "".join(parts)

    try:
        return float(text)
    except ValueError:
        return np.nan

def parse_boolean(value):
    if pd.isna(value):
        return pd.NA

    text = str(value).strip().casefold()
    true_values = {"ja", "j", "yes", "y", "true", "t", "1", "wahr", "available"}
    false_values = {"nein", "n", "no", "false", "f", "0", "falsch", "unavailable"}

    if text in true_values:
        return True
    if text in false_values:
        return False
    return pd.NA

df["price_eur"] = df["price_eur"].map(parse_price).astype("float64")
df["in_stock"] = df["in_stock"].map(parse_boolean).astype("boolean")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)