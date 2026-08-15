import os
import re
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai/products/output.parquet"

df = pd.read_csv(input_path)

def parse_price(value):
    if pd.isna(value):
        return np.nan

    text = str(value).strip()
    text = re.sub(r"[^\d,.\-+]", "", text)

    if not text or text in {"+", "-"}:
        return np.nan

    last_comma = text.rfind(",")
    last_dot = text.rfind(".")

    if last_comma >= 0 and last_dot >= 0:
        decimal_pos = max(last_comma, last_dot)
        integer_part = re.sub(r"[,.]", "", text[:decimal_pos])
        decimal_part = re.sub(r"[,.]", "", text[decimal_pos + 1:])
        normalized = integer_part + "." + decimal_part
    elif last_comma >= 0:
        normalized = text.replace(".", "").replace(",", ".")
    elif last_dot >= 0:
        normalized = text.replace(",", "")
    else:
        normalized = text

    return pd.to_numeric(normalized, errors="coerce")

df["price_eur"] = df["price_eur"].map(parse_price).astype("float64")

stock_mapping = {
    "ja": True,
    "yes": True,
    "true": True,
    "1": True,
    "y": True,
    "j": True,
    "wahr": True,
    "nein": False,
    "no": False,
    "false": False,
    "0": False,
    "n": False,
    "falsch": False,
}

stock_normalized = (
    df["in_stock"]
    .astype("string")
    .str.strip()
    .str.lower()
)

df["in_stock"] = stock_normalized.map(stock_mapping).astype("boolean")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)