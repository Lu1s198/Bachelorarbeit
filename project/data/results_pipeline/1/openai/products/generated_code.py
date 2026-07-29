import os
import csv
import re
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/products_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/openai/products/output.parquet"

with open(input_path, "r", encoding="utf-8-sig", newline="") as f:
    sample = f.read(8192)
    try:
        delimiter = csv.Sniffer().sniff(sample, delimiters=",;|\t").delimiter
    except csv.Error:
        delimiter = ","

df = pd.read_csv(input_path, sep=delimiter, encoding="utf-8-sig")

def parse_price(value):
    if pd.isna(value):
        return np.nan

    text = str(value).strip()
    text = re.sub(r"(?i)(eur|€)", "", text)
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"[^0-9,.\-]", "", text)

    if not text or text in {"-", ".", ",", "-.", "-,"}:
        return np.nan

    comma_count = text.count(",")
    dot_count = text.count(".")

    if comma_count and dot_count:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif comma_count:
        if comma_count == 1:
            before, after = text.rsplit(",", 1)
            if len(after) in (1, 2):
                text = before.replace(",", "") + "." + after
            else:
                text = text.replace(",", "")
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

    return pd.to_numeric(text, errors="coerce")

def parse_boolean(value):
    if pd.isna(value):
        return pd.NA

    text = str(value).strip().lower()
    true_values = {"ja", "j", "true", "t", "1", "yes", "y", "wahr", "available"}
    false_values = {"nein", "n", "false", "f", "0", "no", "falsch", "unavailable"}

    if text in true_values:
        return True
    if text in false_values:
        return False
    return pd.NA

df["price_eur"] = df["price_eur"].apply(parse_price).astype("float64")
df["in_stock"] = df["in_stock"].apply(parse_boolean).astype("boolean")

required_columns = ["product_id", "name", "category", "price_eur", "in_stock"]
for column in required_columns:
    if column not in df.columns:
        df[column] = pd.NA

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)