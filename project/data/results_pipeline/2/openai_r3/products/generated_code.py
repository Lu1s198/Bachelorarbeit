import os
import re
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r3/products/output.parquet"

df = pd.read_csv(input_path)

def parse_price(value):
    if pd.isna(value):
        return np.nan

    text = str(value).strip()
    text = re.sub(r"(?i)(eur|€)", "", text)
    text = text.replace(" ", "").replace("\u00a0", "")

    match = re.search(r"[-+]?\d[\d.,]*", text)
    if not match:
        return np.nan

    number = match.group(0)
    comma_pos = number.rfind(",")
    dot_pos = number.rfind(".")

    if comma_pos >= 0 and dot_pos >= 0:
        if comma_pos > dot_pos:
            number = number.replace(".", "").replace(",", ".")
        else:
            number = number.replace(",", "")
    elif comma_pos >= 0:
        if number.count(",") > 1:
            parts = number.split(",")
            number = "".join(parts[:-1]) + "." + parts[-1]
        else:
            number = number.replace(",", ".")
    elif dot_pos >= 0 and number.count(".") > 1:
        parts = number.split(".")
        number = "".join(parts[:-1]) + "." + parts[-1]

    try:
        return float(number)
    except ValueError:
        return np.nan

df["price_eur"] = df["price_eur"].map(parse_price).astype("float64")

stock_mapping = {
    "ja": True,
    "nein": False,
    "true": True,
    "false": False,
    "1": True,
    "0": False,
    "yes": True,
    "no": False,
}

normalized_stock = (
    df["in_stock"]
    .astype("string")
    .str.strip()
    .str.lower()
)

df["in_stock"] = normalized_stock.map(stock_mapping).astype("boolean")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)