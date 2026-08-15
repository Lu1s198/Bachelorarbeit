import os
import re
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_isolated_r3/products/output.parquet"

df = pd.read_csv(input_path)

def parse_price(value):
    if pd.isna(value):
        return np.nan

    text = str(value).strip()
    text = re.sub(r"(?i)\b(eur|euro)\b", "", text)
    text = text.replace("€", "").replace(" ", "")
    text = re.sub(r"[^0-9,.\-+]", "", text)

    if not text or text in {"-", "+", ".", ","}:
        return np.nan

    comma_pos = text.rfind(",")
    dot_pos = text.rfind(".")

    if comma_pos != -1 and dot_pos != -1:
        if comma_pos > dot_pos:
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif comma_pos != -1:
        text = text.replace(",", ".")

    return pd.to_numeric(text, errors="coerce")

def parse_boolean(value):
    if pd.isna(value):
        return pd.NA

    text = str(value).strip().casefold()
    true_values = {"ja", "j", "true", "t", "1", "yes", "y", "wahr"}
    false_values = {"nein", "n", "false", "f", "0", "no", "falsch"}

    if text in true_values:
        return True
    if text in false_values:
        return False
    return pd.NA

df["price_eur"] = df["price_eur"].map(parse_price).astype("float64")
df["in_stock"] = df["in_stock"].map(parse_boolean).astype("boolean")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)