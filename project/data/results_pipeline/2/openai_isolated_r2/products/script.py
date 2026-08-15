import os
import re
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_isolated_r2/products/output.parquet"

df = pd.read_csv(input_path)

def parse_price(value):
    if pd.isna(value):
        return np.nan

    text = str(value).strip()
    if not text:
        return np.nan

    negative = text.startswith("-") or (text.startswith("(") and text.endswith(")"))
    cleaned = re.sub(r"[^0-9,.\-]", "", text).replace("-", "")

    if not cleaned:
        return np.nan

    comma_count = cleaned.count(",")
    dot_count = cleaned.count(".")

    if comma_count > 0 and dot_count > 0:
        last_comma = cleaned.rfind(",")
        last_dot = cleaned.rfind(".")

        if last_comma > last_dot:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif comma_count > 0:
        if comma_count == 1:
            cleaned = cleaned.replace(",", ".")
        else:
            last_comma = cleaned.rfind(",")
            digits_after = len(cleaned) - last_comma - 1
            if digits_after in (1, 2):
                cleaned = cleaned[:last_comma].replace(",", "") + "." + cleaned[last_comma + 1:]
            else:
                cleaned = cleaned.replace(",", "")
    elif dot_count > 1:
        last_dot = cleaned.rfind(".")
        digits_after = len(cleaned) - last_dot - 1
        if digits_after in (1, 2):
            cleaned = cleaned[:last_dot].replace(".", "") + "." + cleaned[last_dot + 1:]
        else:
            cleaned = cleaned.replace(".", "")

    try:
        result = float(cleaned)
        return -result if negative else result
    except ValueError:
        return np.nan

df["price_eur"] = df["price_eur"].map(parse_price).astype("float64")

stock_mapping = {
    "ja": True,
    "yes": True,
    "true": True,
    "1": True,
    "y": True,
    "j": True,
    "nein": False,
    "no": False,
    "false": False,
    "0": False,
    "n": False,
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