import pandas as pd
import numpy as np
import re
import os

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/anthropic_r3/products/output.parquet"

df = pd.read_csv(input_path, dtype={"product_id": "int64", "name": str, "category": str, "price_eur": str, "in_stock": str})

def clean_price(val):
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    s = s.replace("€", "").replace("EUR", "").replace("eur", "").strip()
    s = s.replace(" ", "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return np.nan

def clean_bool(val):
    if pd.isna(val):
        return np.nan
    s = str(val).strip().lower()
    if s in ["ja", "true", "1", "yes", "y", "wahr"]:
        return True
    elif s in ["nein", "false", "0", "no", "n", "falsch"]:
        return False
    else:
        return np.nan

df["price_eur"] = df["price_eur"].apply(clean_price).astype(float)
df["in_stock"] = df["in_stock"].apply(clean_bool).astype("boolean")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)