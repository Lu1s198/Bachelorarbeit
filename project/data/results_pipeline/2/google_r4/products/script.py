import os
import re
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/synthetic/2/products_raw.csv"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r4/products/output.parquet"

df = pd.read_csv(input_path)


def clean_price(val):
    if pd.isna(val):
        return None
    val = str(val).strip()
    val = re.sub(r"[^\d.,\-]", "", val)
    if not val:
        return None
    if "." in val and "," in val:
        if val.rfind(",") > val.rfind("."):
            val = val.replace(".", "").replace(",", ".")
        else:
            val = val.replace(",", "")
    elif "," in val:
        val = val.replace(",", ".")
    try:
        return float(val)
    except ValueError:
        return None


df["price_eur"] = df["price_eur"].apply(clean_price)

stock_map = {
    "ja": True,
    "true": True,
    "1": True,
    "yes": True,
    "j": True,
    "t": True,
    "wahr": True,
    "nein": False,
    "false": False,
    "0": False,
    "no": False,
    "n": False,
    "f": False,
    "falsch": False,
}

df["in_stock"] = (
    df["in_stock"].astype(str).str.strip().str.lower().map(stock_map)
)
df["in_stock"] = df["in_stock"].astype("bool")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)