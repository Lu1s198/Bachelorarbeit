import os
import re
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r4/products/output.parquet"

df = pd.read_csv(input_path)

def parse_price(value):
    if pd.isna(value):
        return np.nan

    text = str(value).strip()
    if not text:
        return np.nan

    text = re.sub(r"[^0-9,.\-+]", "", text)

    if not text or text in {"+", "-", ".", ","}:
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

    try:
        return float(text)
    except ValueError:
        return np.nan

boolean_mapping = {
    "ja": True,
    "j": True,
    "yes": True,
    "y": True,
    "true": True,
    "t": True,
    "1": True,
    "wahr": True,
    "nein": False,
    "n": False,
    "no": False,
    "false": False,
    "f": False,
    "0": False,
    "falsch": False,
}

df["price_eur"] = df["price_eur"].map(parse_price).astype("float64")
df["in_stock"] = (
    df["in_stock"]
    .astype("string")
    .str.strip()
    .str.lower()
    .map(boolean_mapping)
    .astype("boolean")
)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)