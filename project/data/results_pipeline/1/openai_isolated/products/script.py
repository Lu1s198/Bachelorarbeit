import os
import re
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/products_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai_isolated/products/output.parquet"

df = pd.read_csv(input_path)

def parse_price(value):
    if pd.isna(value):
        return np.nan

    text = str(value).strip()
    text = re.sub(r"[^0-9,.\-+]", "", text)

    if not text or text in {"-", "+", ".", ","}:
        return np.nan

    sign = ""
    if text[0] in {"-", "+"}:
        sign = text[0]
        text = text[1:]

    last_comma = text.rfind(",")
    last_dot = text.rfind(".")

    if last_comma >= 0 and last_dot >= 0:
        decimal_pos = max(last_comma, last_dot)
        integer_part = re.sub(r"[,.]", "", text[:decimal_pos])
        decimal_part = re.sub(r"[,.]", "", text[decimal_pos + 1:])
        normalized = f"{sign}{integer_part}.{decimal_part}"
    elif last_comma >= 0:
        parts = text.split(",")
        if len(parts) > 2:
            normalized = f"{sign}{''.join(parts[:-1])}.{parts[-1]}"
        else:
            normalized = f"{sign}{parts[0]}.{parts[1]}"
    elif last_dot >= 0:
        parts = text.split(".")
        if len(parts) > 2:
            normalized = f"{sign}{''.join(parts[:-1])}.{parts[-1]}"
        else:
            normalized = f"{sign}{parts[0]}.{parts[1]}"
    else:
        normalized = f"{sign}{text}"

    try:
        return float(normalized)
    except ValueError:
        return np.nan

true_values = {"ja", "j", "true", "t", "1", "yes", "y", "wahr"}
false_values = {"nein", "n", "false", "f", "0", "no", "falsch"}

def parse_boolean(value):
    if pd.isna(value):
        return pd.NA

    text = str(value).strip().lower()

    if text in true_values:
        return True
    if text in false_values:
        return False
    return pd.NA

df["price_eur"] = df["price_eur"].map(parse_price).astype("Float64")
df["in_stock"] = df["in_stock"].map(parse_boolean).astype("boolean")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)