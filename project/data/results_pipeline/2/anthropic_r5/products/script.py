import pandas as pd
import numpy as np
import re
import os

df = pd.read_csv("C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv")

def parse_price(val):
    if pd.isna(val):
        return np.nan
    s = str(val)
    s = s.replace("€", "").replace("EUR", "").replace("eur", "").strip()
    s = s.strip()
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    s = re.sub(r"[^0-9.\-]", "", s)
    try:
        return float(s)
    except ValueError:
        return np.nan

def parse_bool(val):
    if pd.isna(val):
        return None
    s = str(val).strip().lower()
    if s in ("ja", "true", "1", "yes", "y", "wahr"):
        return True
    if s in ("nein", "false", "0", "no", "n", "falsch"):
        return False
    return None

df["price_eur"] = df["price_eur"].apply(parse_price)
df["in_stock"] = df["in_stock"].apply(parse_bool).astype("boolean")

df["product_id"] = df["product_id"].astype("int64")
df["name"] = df["name"].astype(str)
df["category"] = df["category"].astype(str)

output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r5/products/output.parquet"
os.makedirs(os.path.dirname(output_path), exist_ok=True)

df.to_parquet(output_path, index=False)