import os
import re
import pandas as pd


def parse_price(val):
    if pd.isna(val):
        return None
    s = str(val)
    s = re.sub(r"[€\s]", "", s)
    s = re.sub(r"EUR", "", s, flags=re.IGNORECASE)
    s = s.replace(",", ".")
    match = re.search(r"\d+(?:\.\d+)?", s)
    if match:
        return float(match.group(0))
    return None


def parse_bool(val):
    if pd.isna(val):
        return None
    s = str(val).strip().lower()
    if s in ["ja", "true", "1", "yes", "wahr"]:
        return True
    if s in ["nein", "false", "0", "no", "falsch"]:
        return False
    return None


input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_isolated_r3/products/output.parquet"

df = pd.read_csv(input_path)

df["price_eur"] = df["price_eur"].apply(parse_price).astype("float64")
df["in_stock"] = df["in_stock"].apply(parse_bool).astype("boolean")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)