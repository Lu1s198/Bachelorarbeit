from pathlib import Path
import re
import numpy as np
import pandas as pd

input_path = Path(r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/products_raw.csv")
output_path = Path(r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/products/output.parquet")

df = pd.read_csv(input_path, dtype="string", sep=None, engine="python")

required_columns = ["product_id", "name", "category", "price_eur", "in_stock"]
missing_columns = [column for column in required_columns if column not in df.columns]
if missing_columns:
    raise ValueError(f"Missing required columns: {missing_columns}")

def parse_price(value):
    if pd.isna(value):
        return np.nan

    text = str(value).strip()
    if not text:
        return np.nan

    text = text.replace("\u00a0", "").replace(" ", "")
    text = re.sub(r"(?i)(eur|euro|€)", "", text)
    text = re.sub(r"[^0-9,.\-()]", "", text)

    if not text:
        return np.nan

    negative = text.startswith("-") or (text.startswith("(") and text.endswith(")"))
    text = text.replace("-", "").replace("(", "").replace(")", "")

    comma_count = text.count(",")
    dot_count = text.count(".")

    if comma_count and dot_count:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif comma_count:
        if comma_count == 1:
            text = text.replace(",", ".")
        else:
            parts = text.split(",")
            if len(parts[-1]) in (1, 2):
                text = "".join(parts[:-1]) + "." + parts[-1]
            else:
                text = "".join(parts)
    elif dot_count > 1:
        parts = text.split(".")
        if len(parts[-1]) in (1, 2):
            text = "".join(parts[:-1]) + "." + parts[-1]
        else:
            text = "".join(parts)

    try:
        result = float(text)
        return -result if negative else result
    except ValueError:
        return np.nan

df["price_eur"] = df["price_eur"].map(parse_price).astype("float64")

stock_mapping = {
    "ja": True,
    "j": True,
    "yes": True,
    "y": True,
    "true": True,
    "t": True,
    "1": True,
    "x": True,
    "nein": False,
    "n": False,
    "no": False,
    "false": False,
    "f": False,
    "0": False,
}

stock_values = (
    df["in_stock"]
    .astype("string")
    .str.strip()
    .str.lower()
    .replace("", pd.NA)
)

df["in_stock"] = stock_values.map(stock_mapping).astype("boolean")

output_path.parent.mkdir(parents=True, exist_ok=True)
df.to_parquet(output_path, index=False)