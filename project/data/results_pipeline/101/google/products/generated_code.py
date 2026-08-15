import os
import re
import pandas as pd

input_path = (
    "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/101/products_raw.csv"
)
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/101/google/products/output.parquet"

df = pd.read_csv(input_path, dtype=str)


def clean_price(val):
    if pd.isna(val):
        return None
    s = str(val).strip()
    s = re.sub(r"[^\d.,]", "", s)
    if not s:
        return None
    if "." in s and "," in s:
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


def clean_bool(val):
    if pd.isna(val):
        return None
    s = str(val).strip().lower()
    if s in ["ja", "true", "1", "yes", "j", "t", "wahr"]:
        return True
    elif s in ["nein", "false", "0", "no", "n", "f", "falsch"]:
        return False
    return None


df["product_id"] = pd.to_numeric(df["product_id"], errors="coerce").astype(
    "int64"
)
df["price_eur"] = df["price_eur"].apply(clean_price)
df["in_stock"] = df["in_stock"].apply(clean_bool).astype("boolean")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)