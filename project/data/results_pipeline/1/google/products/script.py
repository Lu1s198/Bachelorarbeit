import os
import re
import numpy as np
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/1/products_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/products/output.parquet"

df = pd.read_csv(input_path)

def parse_price(val):
    if pd.isna(val):
        return np.nan
    s = str(val).strip()
    s = re.sub(r"[^\d.,]", "", s)
    if not s:
        return np.nan
    if "." in s and "," in s:
        if s.rfind(".") < s.rfind(","):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return np.nan

def parse_bool(val):
    if pd.isna(val):
        return False
    s = str(val).strip().lower()
    if s in ["ja", "true", "1", "1.0", "yes", "y", "wahr"]:
        return True
    if s in ["nein", "false", "0", "0.0", "no", "n", "falsch"]:
        return False
    return False

df["price_eur"] = df["price_eur"].apply(parse_price)
df["in_stock"] = df["in_stock"].apply(parse_bool).astype(bool)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)