import os
import re
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/products_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/products/output.parquet"

df = pd.read_csv(input_path)

def parse_price(value):
    if pd.isna(value):
        return np.nan

    text = str(value).strip()
    text = re.sub(r"(?i)\b(?:eur|euro)\b", "", text)
    text = text.replace("€", "")
    text = re.sub(r"[^0-9,.\-+]", "", text)

    if not text or text in {"-", "+", ".", ","}:
        return np.nan

    comma_positions = [m.start() for m in re.finditer(",", text)]
    dot_positions = [m.start() for m in re.finditer(r"\.", text)]

    if comma_positions and dot_positions:
        decimal_separator = "," if comma_positions[-1] > dot_positions[-1] else "."
        thousands_separator = "." if decimal_separator == "," else ","
        text = text.replace(thousands_separator, "")
        text = text.replace(decimal_separator, ".")
    elif comma_positions or dot_positions:
        separator = "," if comma_positions else "."
        parts = text.split(separator)

        if len(parts) > 1:
            last_part = parts[-1]
            preceding_parts = parts[:-1]

            if len(last_part) == 3 and all(len(part.lstrip("+-")) <= 3 for part in preceding_parts):
                text = "".join(parts)
            else:
                text = "".join(preceding_parts) + "." + last_part

    try:
        return float(text)
    except ValueError:
        return np.nan

price_values = df["price_eur"].map(parse_price)
df["price_eur"] = pd.Series(price_values, index=df.index, dtype="Float64")

stock_mapping = {
    "ja": True,
    "yes": True,
    "true": True,
    "1": True,
    "wahr": True,
    "y": True,
    "nein": False,
    "no": False,
    "false": False,
    "0": False,
    "falsch": False,
    "n": False,
}

stock_normalized = (
    df["in_stock"]
    .astype("string")
    .str.strip()
    .str.lower()
    .map(stock_mapping)
)
df["in_stock"] = stock_normalized.astype("boolean")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)