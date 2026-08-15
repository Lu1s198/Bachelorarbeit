import os
import re
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/101/products_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/openai_isolated/products/output.parquet"

df = pd.read_csv(input_path)

def parse_price(value):
    if pd.isna(value):
        return np.nan

    text = str(value).strip()
    text = text.replace("\u00a0", "").replace(" ", "")
    text = re.sub(r"(?i)(eur|euro|€)", "", text)
    text = re.sub(r"[^0-9,.\-+()]", "", text)

    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("()")

    if not text:
        return np.nan

    comma_pos = text.rfind(",")
    dot_pos = text.rfind(".")

    if comma_pos != -1 and dot_pos != -1:
        if comma_pos > dot_pos:
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif comma_pos != -1:
        text = text.replace(".", "").replace(",", ".")
    elif text.count(".") > 1:
        last_dot = text.rfind(".")
        text = text[:last_dot].replace(".", "") + text[last_dot:]

    try:
        result = float(text)
        return -result if negative else result
    except ValueError:
        return np.nan

def parse_boolean(value):
    if pd.isna(value):
        return pd.NA

    text = str(value).strip().casefold()
    true_values = {"ja", "j", "yes", "y", "true", "t", "1", "wahr", "on"}
    false_values = {"nein", "n", "no", "false", "f", "0", "falsch", "off"}

    if text in true_values:
        return True
    if text in false_values:
        return False
    return pd.NA

df["price_eur"] = df["price_eur"].map(parse_price).astype("float64")
df["in_stock"] = df["in_stock"].map(parse_boolean).astype("boolean")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)