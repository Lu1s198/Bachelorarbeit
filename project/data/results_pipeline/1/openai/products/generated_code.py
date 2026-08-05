import os
import re
import csv
import pandas as pd
import numpy as np

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/products_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/products/output.parquet"

def read_csv_robust(path):
    encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252"]
    for encoding in encodings:
        try:
            with open(path, "r", encoding=encoding, newline="") as f:
                sample = f.read(8192)
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=",;|\t")
                    separator = dialect.delimiter
                except csv.Error:
                    separator = ","
            return pd.read_csv(path, sep=separator, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path)

def parse_price(value):
    if pd.isna(value):
        return np.nan

    text = str(value).strip().lower()
    if not text:
        return np.nan

    negative = text.startswith("-") or (text.startswith("(") and text.endswith(")"))
    cleaned = re.sub(r"[^0-9,.\-]", "", text).replace("-", "")

    if not cleaned or not re.search(r"\d", cleaned):
        return np.nan

    comma_positions = [m.start() for m in re.finditer(",", cleaned)]
    dot_positions = [m.start() for m in re.finditer(r"\.", cleaned)]

    if comma_positions and dot_positions:
        if comma_positions[-1] > dot_positions[-1]:
            normalized = cleaned.replace(".", "").replace(",", ".")
        else:
            normalized = cleaned.replace(",", "")
    elif comma_positions:
        parts = cleaned.split(",")
        normalized = "".join(parts[:-1]) + "." + parts[-1] if len(parts) > 1 else cleaned
    else:
        normalized = cleaned

    try:
        number = float(normalized)
        return -number if negative else number
    except ValueError:
        return np.nan

df = read_csv_robust(input_path)

if "price_eur" in df.columns:
    df["price_eur"] = df["price_eur"].map(parse_price).astype("float64")
else:
    df["price_eur"] = pd.Series(np.nan, index=df.index, dtype="float64")

if "in_stock" in df.columns:
    normalized_stock = (
        df["in_stock"]
        .astype("string")
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", "", regex=True)
    )
    stock_mapping = {
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
    df["in_stock"] = normalized_stock.map(stock_mapping).astype("boolean")
else:
    df["in_stock"] = pd.Series(pd.NA, index=df.index, dtype="boolean")

for column in ["product_id", "name", "category"]:
    if column not in df.columns:
        df[column] = pd.NA

required_columns = ["product_id", "name", "category", "price_eur", "in_stock"]
remaining_columns = [column for column in df.columns if column not in required_columns]
df = df[required_columns + remaining_columns]

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)