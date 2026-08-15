from pathlib import Path
import re
import numpy as np
import pandas as pd

input_path = Path(r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv")
output_path = Path(r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/openai_r5/products/output.parquet")

df = pd.read_csv(input_path)

def parse_price(value):
    if pd.isna(value):
        return np.nan

    text = str(value).strip()
    text = re.sub(r"(?i)(eur|€)", "", text)
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[^0-9,.\-+]", "", text)

    if not text:
        return np.nan

    last_comma = text.rfind(",")
    last_dot = text.rfind(".")

    if last_comma >= 0 and last_dot >= 0:
        if last_comma > last_dot:
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif last_comma >= 0:
        parts = text.split(",")
        if len(parts) > 2:
            text = "".join(parts[:-1]) + "." + parts[-1]
        elif len(parts) == 2 and len(parts[1]) == 3 and len(parts[0]) > 3:
            text = "".join(parts)
        else:
            text = text.replace(",", ".")
    elif last_dot >= 0:
        parts = text.split(".")
        if len(parts) > 2:
            text = "".join(parts[:-1]) + "." + parts[-1]

    return pd.to_numeric(text, errors="coerce")

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

df["in_stock"] = (
    df["in_stock"]
    .astype("string")
    .str.strip()
    .str.lower()
    .map(stock_mapping)
    .astype("boolean")
)

output_path.parent.mkdir(parents=True, exist_ok=True)
df.to_parquet(output_path, index=False)