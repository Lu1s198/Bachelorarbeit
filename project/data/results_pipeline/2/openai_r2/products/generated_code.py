import os
import re
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r2/products/output.parquet"

df = pd.read_csv(input_path)

def parse_price(value):
    if pd.isna(value):
        return np.nan

    text = str(value).strip()
    if not text:
        return np.nan

    negative = text.startswith("-") or (text.startswith("(") and text.endswith(")"))
    text = re.sub(r"[^0-9,.\-+]", "", text)
    text = text.replace("+", "").replace("-", "")

    if not text:
        return np.nan

    comma_positions = [m.start() for m in re.finditer(",", text)]
    dot_positions = [m.start() for m in re.finditer(r"\.", text)]

    if comma_positions and dot_positions:
        decimal_pos = max(comma_positions[-1], dot_positions[-1])
        decimal_sep = text[decimal_pos]
        integer_part = re.sub(r"[,.]", "", text[:decimal_pos])
        fractional_part = re.sub(r"[,.]", "", text[decimal_pos + 1:])
        normalized = integer_part + "." + fractional_part
    elif comma_positions:
        parts = text.split(",")
        if len(parts) == 2 and len(parts[-1]) in (1, 2):
            normalized = parts[0].replace(".", "") + "." + parts[1]
        elif len(parts) > 1 and len(parts[-1]) in (1, 2):
            normalized = "".join(parts[:-1]).replace(".", "") + "." + parts[-1]
        else:
            normalized = "".join(parts)
    elif dot_positions:
        parts = text.split(".")
        if len(parts) == 2 and len(parts[-1]) in (1, 2):
            normalized = parts[0] + "." + parts[1]
        elif len(parts) > 1 and len(parts[-1]) in (1, 2):
            normalized = "".join(parts[:-1]) + "." + parts[-1]
        else:
            normalized = "".join(parts)
    else:
        normalized = text

    try:
        result = float(normalized)
        return -result if negative else result
    except ValueError:
        return np.nan

price_values = df["price_eur"].map(parse_price)
df["price_eur"] = pd.to_numeric(price_values, errors="coerce").astype("float64")

stock_mapping = {
    "ja": True,
    "yes": True,
    "true": True,
    "1": True,
    "wahr": True,
    "y": True,
    "j": True,
    "nein": False,
    "no": False,
    "false": False,
    "0": False,
    "falsch": False,
    "n": False,
}

stock_normalized = df["in_stock"].astype("string").str.strip().str.lower()
df["in_stock"] = stock_normalized.map(stock_mapping).astype("boolean")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)