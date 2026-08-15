import os
import re
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_isolated_r5/products/output.parquet"

df = pd.read_csv(input_path)


def parse_price(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    s = re.sub(r"[^\d.,-]", "", s)
    if not s:
        return None
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def parse_bool(val):
    if pd.isna(val):
        return None
    s = str(val).strip().lower()
    if s in ["ja", "true", "1", "yes", "y", "wahr", "t"]:
        return True
    elif s in ["nein", "false", "0", "no", "n", "falsch", "f"]:
        return False
    return None


df["price_eur"] = df["price_eur"].apply(parse_price)
df["in_stock"] = df["in_stock"].apply(parse_bool).astype("boolean")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)