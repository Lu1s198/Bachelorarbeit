import os
import re
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/101/products_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/openai/products/output.parquet"

df = pd.read_csv(
    input_path,
    dtype={
        "product_id": "int64",
        "name": "string",
        "category": "string",
        "price_eur": "string",
        "in_stock": "string",
    },
)

def parse_price(value):
    if pd.isna(value):
        return np.nan

    text = str(value).strip()
    text = re.sub(r"(?i)(eur|euro)", "", text)
    text = text.replace("€", "")
    text = re.sub(r"[^\d,.\-+]", "", text)

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
        if comma_count > 1:
            parts = text.split(",")
            if all(len(part) == 3 for part in parts[1:]):
                text = "".join(parts)
            else:
                text = "".join(parts[:-1]) + "." + parts[-1]
        else:
            text = text.replace(",", ".")
    elif dot_count > 1:
        parts = text.split(".")
        if all(len(part) == 3 for part in parts[1:]):
            text = "".join(parts)
        else:
            text = "".join(parts[:-1]) + "." + parts[-1]

    try:
        return float(text)
    except ValueError:
        return np.nan

df["price_eur"] = df["price_eur"].map(parse_price).astype("float64")

stock_map = {
    "ja": True,
    "yes": True,
    "true": True,
    "1": True,
    "y": True,
    "wahr": True,
    "nein": False,
    "no": False,
    "false": False,
    "0": False,
    "n": False,
    "falsch": False,
}

normalized_stock = (
    df["in_stock"]
    .astype("string")
    .str.strip()
    .str.lower()
)

df["in_stock"] = normalized_stock.map(stock_map).astype("boolean")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)