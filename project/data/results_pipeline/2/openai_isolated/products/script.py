import os
import re
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_isolated/products/output.parquet"

df = pd.read_csv(input_path)

def parse_price(value):
    if pd.isna(value):
        return np.nan
    text = str(value).strip().lower()
    text = re.sub(r"[^0-9,.\-+]", "", text)
    if not text:
        return np.nan

    last_comma = text.rfind(",")
    last_dot = text.rfind(".")

    if last_comma != -1 and last_dot != -1:
        if last_comma > last_dot:
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif last_comma != -1:
        text = text.replace(",", ".")

    try:
        return float(text)
    except ValueError:
        return np.nan

def parse_boolean(value):
    if pd.isna(value):
        return pd.NA
    text = str(value).strip().lower()
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