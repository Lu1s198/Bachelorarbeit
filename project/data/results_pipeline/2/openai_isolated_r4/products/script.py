import os
import re
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_isolated_r4/products/output.parquet"

df = pd.read_csv(input_path)

def parse_price(value):
    if pd.isna(value):
        return np.nan

    text = str(value).strip()
    if not text:
        return np.nan

    negative = "-" in text or "(" in text and ")" in text
    number = re.sub(r"[^0-9.,]", "", text)

    if not number:
        return np.nan

    if "," in number and "." in number:
        if number.rfind(",") > number.rfind("."):
            number = number.replace(".", "").replace(",", ".")
        else:
            number = number.replace(",", "")
    elif "," in number:
        if number.count(",") > 1:
            parts = number.split(",")
            number = "".join(parts[:-1]) + "." + parts[-1]
        else:
            number = number.replace(",", ".")
    elif number.count(".") > 1:
        parts = number.split(".")
        number = "".join(parts[:-1]) + "." + parts[-1]

    try:
        result = float(number)
        return -result if negative and result > 0 else result
    except ValueError:
        return np.nan

df["price_eur"] = df["price_eur"].map(parse_price).astype("float64")

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

stock_normalized = (
    df["in_stock"]
    .astype("string")
    .str.strip()
    .str.casefold()
)

df["in_stock"] = stock_normalized.map(stock_mapping).astype("boolean")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)